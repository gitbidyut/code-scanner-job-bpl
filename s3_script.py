import boto3

# Hardcoded credentials - DANGEROUS PRACTICE
AWS_ACCESS_KEY = "AKIAXXXXXXXXXXXXXXXX"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_REGION = "us-east-1"

def list_s3_buckets():
    try:
        # Initialize the S3 client with hardcoded credentials
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )

        # Call S3 to list buckets
        response = s3.list_buckets()

        print("Buckets:")
        for bucket in response['Buckets']:
            print(f'  {bucket["Name"]}')

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_s3_buckets()
