from google.cloud import storage

class GCSStorage:
    def __init__(self, bucket_name: str):
        if not bucket_name:
            raise ValueError("bucket_name cannot be None")

        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def upload_file(
            self,
            local_path: str,
            object_name: str,
            content_type: str | None = None,
    ) -> str:
        blob = self.bucket.blob(object_name)
        blob.upload_from_filename(local_path, content_type=content_type)
        return (
            f"gs://{self.bucket.name}/{object_name}"
        )
