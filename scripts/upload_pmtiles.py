import boto3
from pathlib import Path

ACCOUNT_ID = "YOUR_ACCOUNT_ID"
ACCESS_KEY = "YOUR_ACCESS_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"
BUCKET = "denetzpop-tiles"
FILE = Path(r"C:\Users\KitCat\Desktop\v1.420\map-app\germany_pop.pmtiles")
KEY = "germany_pop.pmtiles"

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
)

size_mb = FILE.stat().st_size / 1024 / 1024
print(f"Uploading {FILE.name} ({size_mb:.1f} MB) to R2 bucket '{BUCKET}'...")

s3.upload_file(
    str(FILE),
    BUCKET,
    KEY,
    Config=boto3.s3.transfer.TransferConfig(multipart_threshold=50 * 1024 * 1024, multipart_chunksize=50 * 1024 * 1024),
    Callback=lambda bytes_transferred: None,
)

print(f"Done. Object '{KEY}' uploaded to bucket '{BUCKET}'.")
print(f"Public URL (after enabling public access): https://pub-{ACCOUNT_ID}.r2.dev/{KEY}")
