# -*- coding: utf-8 -*-

import io
import base64
import json
import zipfile
import unicodedata

from odoo import _, fields, http
from odoo.addons.mail.controllers.discuss import DiscussController
from odoo.addons.web.controllers.binary import Binary
from odoo.exceptions import AccessError
from odoo.http import content_disposition, request
from odoo.tools import replace_exceptions


class CloudFilesController(DiscussController):
    """
    Controller to manage attachments operations in file manager
    """

    @http.route("/cloud_base/folder", methods=["POST"], type="json", auth="user")
    def cloud_base_check_object_folder(self, thread_model, thread_id, **kwargs):
        """
        Check if a cloud folder exists for the given model and ID

        Returns:
            bool: True if folder exists, False otherwise
        """
        folder_exists = request.env["clouds.folder"].search_count(
            [("res_model", "=", thread_model), ("res_id", "=", thread_id)],
            limit=1
        )
        return bool(folder_exists)

    @http.route("/cloud_base/attachments/data", methods=["POST"], type="json", auth="user")
    def cloud_base_folder_attachments(self, thread_model, thread_id, checked_folder, folder_domain, **kwargs):
        """
        Get attachments data for a thread or folder

        Returns:
            list: Formatted attachment data
        """
        thread = request.env[thread_model].with_context(active_test=False).browse(thread_id)
        if not checked_folder:
            folder_domain = [("res_id", "=", thread_id), ("res_model", "=", thread_model)]
        attachments = request.env["ir.attachment"].search(folder_domain, order="id desc")
        return attachments._attachment_format()

    @http.route("/cloud_base/upload_attachment", type="http", auth="user")
    def upload_to_file_manager(self, clouds_folder_id, ufile, callback=None):
        """
        Upload files to cloud folder

        Args:
            clouds_folder_id (str): ID of the target folder
            ufile (UploadedFile): File to upload
            callback (str, optional): JS callback function name

        Returns:
            Response: JSON response or script for callback
        """
        out = """<script language="javascript" type="text/javascript">
            var win = window.top.window;
            win.jQuery(win).trigger(%s, %s);
        </script>"""
        args = []

        if not clouds_folder_id or clouds_folder_id == "false":
            args.append({"error": _("Please select a folder for uploaded files")})
        else:
            files = request.httprequest.files.getlist("ufile")
            Model = request.env["ir.attachment"].with_context(
                disable_binary_fields_checks=True  # Important for Odoo 17
            )

            for ufile in files:
                filename = ufile.filename
                if request.httprequest.user_agent.browser == "safari":
                    filename = unicodedata.normalize("NFD", ufile.filename)

                try:
                    attachment = Model.create({
                        "name": filename,
                        "raw": ufile.read(),  # Changed from datas to raw in Odoo 17
                        "clouds_folder_id": int(clouds_folder_id),  # Ensure integer
                    })
                    attachment._post_add_create()
                    args.append({
                        "filename": Binary._clean(filename),
                        "mimetype": ufile.content_type,
                        "id": attachment.id,
                        "size": attachment.file_size
                    })
                except AccessError:
                    args.append({"error": _("You are not allowed to upload an attachment here.")})
                except Exception as e:
                    args.append({"error": _("Something went wrong: %s") % str(e)})

        if callback:
            return out % (json.dumps(Binary._clean(callback)), json.dumps(args))
        return json.dumps(args)

    @http.route("/cloud_base/multiupload/<string:attachments>", type="http", auth="user")
    def multi_download_file_manager(self, attachments, **kwargs):
        """
        Download multiple attachments as a zip archive

        Args:
            attachments (str): Comma-separated attachment IDs

        Returns:
            Response: Zip file response
        """
        attachment_ids = []
        if attachments:
            attachment_ids = [int(art) for art in attachments.split(",")]

        attachments = request.env["ir.attachment"].browse(attachment_ids).exists()
        stream = io.BytesIO()

        try:
            with zipfile.ZipFile(stream, "w") as zip_archive:
                for attachment in attachments:
                    if attachment.type == "binary" or (attachment.type == "url" and attachment.cloud_key):
                        binary_stream = request.env["ir.binary"]._get_stream_from(attachment)
                        zip_archive.writestr(
                            binary_stream.download_name,
                            binary_stream.read(),
                            compress_type=zipfile.ZIP_DEFLATED
                        )
        except zipfile.BadZipfile:
            pass

        content = stream.getvalue()
        archive_title = kwargs.get("archive_name") or str(fields.Datetime.now())
        headers = [
            ("Content-Type", "application/octet-stream"),  # More compatible than application/zip
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Length", len(content)),
            ("Content-Disposition", content_disposition(f"{archive_title}.zip"))
        ]
        return request.make_response(content, headers)

    @http.route("/cloud_base/folder_upload/<model('clouds.folder'):folder_id>", type="http", auth="user")
    def folder_download_file_manager(self, folder_id, **kwargs):
        """
        Download all attachments from a cloud folder as zip

        Args:
            folder_id (clouds.folder): Folder to download

        Returns:
            Response: Zip file response
        """
        attachment_ids = request.env["ir.attachment"].search(
            [("clouds_folder_id", "=", folder_id.id)]
        ).ids
        att_param = ",".join(str(at) for at in attachment_ids)
        return self.multi_download_file_manager(att_param, archive_name=folder_id.name)

    @http.route("/cloud_base/export_logs", type="http", auth="user")
    def cloud_base_export_logs(self, search_name, selected_clients, log_levels):
        """
        Export logs as a text file

        Args:
            search_name (str): Search filter
            selected_clients (str): JSON string of client IDs
            log_levels (str): JSON string of log levels

        Returns:
            Response: Text file response
        """
        content = request.env["clouds.log"]._prepare_txt_logs(
            search_name,
            json.loads(selected_clients),
            json.loads(log_levels)
        ).encode("utf-8")

        headers = [
            ("Content-Type", "text/plain; charset=utf-8"),  # Explicit charset
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Length", len(content)),
            ("Content-Disposition", content_disposition(f"cloud_logs_{fields.Datetime.now()}.txt"))
        ]
        return request.make_response(content, headers)