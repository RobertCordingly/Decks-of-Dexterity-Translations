import boto3
import os

# Configuration
bucket_name = 'decksofdexterity'
prefix = 'translations/'
local_folder = '../recent_changes'

# Ensure the local folder exists
os.makedirs(local_folder, exist_ok=True)

# Initialize S3 client
s3 = boto3.client('s3')

# List all JSON files in the prefix
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
if 'Contents' in response:
    for obj in response['Contents']:
        key = obj['Key']
        if key.endswith('.json'):
            filename = os.path.basename(key)
            local_path = os.path.join(local_folder, filename)
            s3.download_file(bucket_name, key, local_path)
            s3.delete_object(Bucket=bucket_name, Key=key)
            print(f'Downloaded and deleted: {key} -> {local_path}')
else:
    print('No files found in the specified S3 prefix.')
