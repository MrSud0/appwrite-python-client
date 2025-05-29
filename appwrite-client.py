import yaml
import sys
import os
import urllib3
import requests
from dotenv import load_dotenv
import time
import mimetypes
from pathlib import Path
import json

# Load environment variables from .env file
load_dotenv()

def load_yaml_data(file_path):
    """Load data from a YAML file"""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading YAML file: {str(e)}")
        sys.exit(1)

def create_session(email, password, project_id, endpoint, verify_ssl=True):
    """Create an authenticated requests session"""
    
    # Create a requests session for handling cookies
    session = requests.Session()
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False
    
    # Login
    login_url = f"{endpoint}/account/sessions/email"
    login_headers = {
        "X-Appwrite-Project": project_id,
        "Content-Type": "application/json"
    }
    login_data = {
        "email": email,
        "password": password
    }
    
    response = session.post(login_url, headers=login_headers, json=login_data)
    
    if response.status_code != 201:
        print(f"❌ Login failed: {response.text}")
        return None
    
    print(f"✅ Login successful!")
    return session

def test_connection_with_session(session, project_id, endpoint):
    """Test connection to Appwrite by listing databases using requests session"""
    print("Testing connection to Appwrite...")
    
    db_url = f"{endpoint}/databases"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    response = session.get(db_url, headers=headers)
    
    if response.status_code == 200:
        databases = response.json()
        print(f"✅ Connection successful! Found {len(databases['databases'])} databases")
        return True
    else:
        print(f"❌ Connection test failed: {response.text}")
        return False

def check_database_with_session(session, project_id, database_id, endpoint):
    """Check if database exists and is accessible using requests session"""
    print(f"Checking database (ID: {database_id})...")
    
    db_url = f"{endpoint}/databases/{database_id}"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    response = session.get(db_url, headers=headers)
    
    if response.status_code == 200:
        database = response.json()
        print(f"✅ Database found: '{database['name']}' (ID: {database['$id']})")
        return True
    else:
        # In case of permission error, try a more basic operation
        try:
            # Try listing databases instead, which might require lower permissions
            list_url = f"{endpoint}/databases"
            list_response = session.get(list_url, headers=headers)
            
            if list_response.status_code == 200:
                database_list = list_response.json()
                print(f"✅ Connected to Appwrite and can access database service")
                print(f"Available databases: {len(database_list['databases'])}")
                return True
            else:
                print(f"❌ Database access failed: {list_response.text}")
                return False
        except Exception as e:
            print(f"❌ Database access failed: {str(e)}")
            return False

def get_document_with_session(session, project_id, database_id, collection_id, document_id, endpoint):
    """Retrieve a document from a specific collection using its documentId."""
    url = f"{endpoint}/databases/{database_id}/collections/{collection_id}/documents/{document_id}"
    headers = {"X-Appwrite-Project": project_id}
    response = session.get(url, headers=headers)
    if response.status_code == 200:
        doc = response.json()
        print("✅ Document retrieved successfully:")
        print(doc)
        return doc
    else:
        print(f"❌ Failed to get document (ID: {document_id}): {response.text}")
        return None

def get_collection_documents_with_session(session, project_id, database_id, collection_id, endpoint):
    """Get documents from a collection using an existing session"""
    
    # Get documents
    docs_url = f"{endpoint}/databases/{database_id}/collections/{collection_id}/documents"
    docs_headers = {
        "X-Appwrite-Project": project_id
    }
    
    docs_response = session.get(docs_url, headers=docs_headers)
    
    if docs_response.status_code != 200:
        print(f"❌ Failed to fetch documents: {docs_response.text}")
        return None
    
    documents = docs_response.json()
    print(f"✅ Found {documents['total']} documents in collection")
    return documents

def get_collection_id_by_name(session, project_id, database_id, target_name, endpoint):
    """Retrieve a collection's ID by its name using the Appwrite REST API."""
    url = f"{endpoint}/databases/{database_id}/collections"
    headers = {
        "X-Appwrite-Project": project_id
    }
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to list collections: {response.text}")
        return None
    collections = response.json().get("collections", [])
    for coll in collections:
        if coll.get("name") == target_name:
            return coll.get("$id")
    print(f"Collection with name '{target_name}' not found.")
    return None

def create_document_with_session(session, project_id, database_id, collection_id, data, endpoint):
    """Create a document using an existing session"""
    
    # Create document
    doc_url = f"{endpoint}/databases/{database_id}/collections/{collection_id}/documents"
    doc_headers = {
        "X-Appwrite-Project": project_id,
        "Content-Type": "application/json"
    }
    
    # Use 'unique()' as document ID to let Appwrite generate a unique ID
    doc_data = {
        "documentId": "unique()",
        "data": data
    }
    
    doc_response = session.post(doc_url, headers=doc_headers, json=doc_data)
    
    if doc_response.status_code != 201:
        print(f"❌ Failed to create document: {doc_response.text}")
        return None
    
    result = doc_response.json()
    print(f"✅ Document created successfully with ID: {result['$id']}")
    return result

def bulk_create_documents_with_session(session, yaml_file, project_id, database_id, collection_id, endpoint):
    """Create documents in bulk from YAML data using an existing session"""
    # Load data from YAML
    data = load_yaml_data(yaml_file)
    
    # Process documents
    successful = 0
    failed = 0
    errors = []
    
    print(f"Starting bulk upload to database ID: {database_id}, collection ID: {collection_id}")
    
    for idx, document_data in enumerate(data, 1):
        try:
            # Create document
            doc_url = f"{endpoint}/databases/{database_id}/collections/{collection_id}/documents"
            doc_headers = {
                "X-Appwrite-Project": project_id,
                "Content-Type": "application/json"
            }
            
            # Use 'unique()' as document ID to let Appwrite generate a unique ID
            doc_data = {
                "documentId": "unique()",
                "data": document_data
            }
            
            doc_response = session.post(doc_url, headers=doc_headers, json=doc_data)
            
            if doc_response.status_code != 201:
                failed += 1
                error_msg = f"Error creating document {idx}: {doc_response.text}"
                errors.append(error_msg)
                print(error_msg)
                continue
            
            result = doc_response.json()
            successful += 1
            print(f"Created document {idx}/{len(data)}: ID {result['$id']}")
            
        except Exception as e:
            failed += 1
            error_msg = f"Error creating document {idx}: {str(e)}"
            errors.append(error_msg)
            print(error_msg)
        time.sleep(0.2)
    
    # Print summary
    print("\n--- Upload Summary ---")
    print(f"Total documents: {len(data)}")
    print(f"Successfully created: {successful}")
    print(f"Failed: {failed}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"- {error}")

def delete_document_with_session(session, project_id, database_id, collection_id, document_id, endpoint):
    """Delete a specific document using an existing session."""
    url = f"{endpoint}/databases/{database_id}/collections/{collection_id}/documents/{document_id}"
    headers = {"X-Appwrite-Project": project_id}
    response = session.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"✅ Document {document_id} deleted successfully.")
        return True
    else:
        print(f"❌ Failed to delete document {document_id}: {response.text}")
        return False

def delete_all_documents_with_session(session, project_id, database_id, collection_id, endpoint):
    """Delete all documents in the specified collection using an existing session."""
    documents = get_collection_documents_with_session(session, project_id, database_id, collection_id, endpoint)
    if not documents or documents.get("total", 0) == 0:
        print("No documents found to delete.")
        return
    for doc in documents.get("documents", []):
        doc_id = doc["$id"]
        delete_document_with_session(session, project_id, database_id, collection_id, doc_id, endpoint)

def update_document_with_session(session, project_id, database_id, collection_id, document_id, data, endpoint):
    """Update a specific document using an existing session."""
    url = f"{endpoint}/databases/{database_id}/collections/{collection_id}/documents/{document_id}"
    headers = {
        "X-Appwrite-Project": project_id,
        "Content-Type": "application/json"
    }
    payload = {"data": data}
    response = session.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Document {document_id} updated successfully.")
        return result
    else:
        print(f"❌ Failed to update document {document_id}: {response.text}")
        return None

def bulk_update_documents_with_session(session, yaml_file, project_id, database_id, collection_id, endpoint):
    """Bulk update documents from YAML data using an existing session.

    Each entry in the YAML file should be a dictionary that includes a 'documentId' key
    for the document to update, along with other key-value pairs representing the fields to update.
    """
    data = load_yaml_data(yaml_file)
    if not data or len(data) == 0:
        print("No data found in YAML file for updating.")
        return
    successful = 0
    failed = 0
    errors = []
    print(f"Starting bulk update for documents in collection {collection_id}")
    for idx, doc_data in enumerate(data, 1):
        if "documentId" not in doc_data:
            print(f"Skipping update for item {idx}: No 'documentId' provided.")
            continue
        document_id = doc_data.pop("documentId")
        result = update_document_with_session(session, project_id, database_id, collection_id, document_id, doc_data, endpoint)
        if result:
            successful += 1
        else:
            failed += 1
            errors.append(f"Error updating document {document_id}")
    print("\n--- Bulk Update Summary ---")
    print(f"Total items processed: {len(data)}")
    print(f"Successfully updated: {successful}")
    print(f"Failed updates: {failed}")
    if errors:
        print("Errors encountered:")
        for error in errors:
            print(f"- {error}")

def _process_images_field(data, session, project_id, bucket_id, endpoint, yaml_dir):
    """Upload image file paths in data and replace them with file IDs."""
    if not bucket_id or 'images' not in data or not isinstance(data['images'], list):
        return

    processed_images = []
    for img in data['images']:
        img_path = Path(str(img))
        if not img_path.is_absolute():
            img_path = Path(yaml_dir) / img_path

        if img_path.exists():
            result = upload_file_to_bucket_with_duplicate_check(
                session,
                project_id,
                bucket_id,
                img_path,
                endpoint
            )
            if result and not result.get('skipped'):
                processed_images.append(result['$id'])
            elif result and result.get('skipped'):
                existing = find_file_by_name_paginated(session, project_id, bucket_id, img_path.name, endpoint)
                if existing:
                    processed_images.append(existing['$id'])
        else:
            processed_images.append(str(img))

    data['images'] = processed_images

def create_documents_with_relationships(session, yaml_file, project_id, database_id, collection_mapping, endpoint, bucket_id=None):
    """
    Process a YAML file with a Children/Parent structure.

    The YAML file should contain two top-level keys:
      - 'Children': a list of child document definitions.
          Each item is a mapping with keys:
             - collection_name: the name of the collection (e.g., "Country", "Space", etc.)
             - data: a dictionary of fields. YAML anchors can be used here.
      - 'Parent': a list of parent document definitions.
          Each item is a mapping with keys:
             - collection_name: the name of the parent collection (e.g., "nezuko")
             - data: a dictionary containing relationship fields that reference one of the child definitions via YAML anchors.

    If `bucket_id` is provided and a parent `data` dictionary contains an `images`
    field with file paths, those images will be uploaded to the specified bucket
    and replaced with their resulting file IDs before the parent document is
    created.
    """
    yaml_data = load_yaml_data(yaml_file)
    if not ("Children" in yaml_data and "Parent" in yaml_data):
        print("YAML file does not contain both 'Children' and 'Parent' sections.")
        return
    
    child_mapping = {}
    print("--- Processing Children ---")
    for child in yaml_data["Children"]:
        coll_name = child.get("collection_name")
        print(f"Processing child collection: {coll_name}")
        data = child.get("data")
        if not coll_name or not data:
            print("Child entry is missing 'collection_name' or 'data'. Skipping.")
            continue
        if coll_name not in collection_mapping:
            print(f"Collection name '{coll_name}' not found in collection mapping. Skipping child.")
            continue
        coll_id = collection_mapping[coll_name]
        result = create_document_with_session(session, project_id, database_id, coll_id, data, endpoint)
        if result is not None:
            # Store the mapping from the data object's id (from YAML) to the document ID returned by Appwrite
            child_mapping[id(data)] = result["$id"]
    
    print("--- Processing Parent ---")
    for parent in yaml_data["Parent"]:
        print(f"Processing parent collection: {parent.get('collection_name')}")
        coll_name = parent.get("collection_name")
        data = parent.get("data")
        if not coll_name or not data:
            print("Parent entry is missing 'collection_name' or 'data'. Skipping.")
            continue
        # Process each field in parent's data
        for key, value in data.items():
            if isinstance(value, dict) and 'value' in value and 'relation' in value:
                child_anchor = value['value']
                relation_type = value['relation']
                if id(child_anchor) in child_mapping:
                    child_doc_id = child_mapping[id(child_anchor)]
                    # Wrap in list for relationship types expecting an array:
                    if relation_type in ["oneToMany", "manyToMany"]:
                        print(f"Replacing relationship field '{key}' with document IDs [{child_doc_id}] based on relation '{relation_type}'")
                        data[key] = [child_doc_id]
                    else:
                        print(f"Replacing relationship field '{key}' with document ID {child_doc_id} based on relation '{relation_type}'")
                        data[key] = child_doc_id
                else:
                    print(f"Could not find a matching child for field '{key}'.")

        # Handle image uploads if needed
        _process_images_field(data, session, project_id, bucket_id, endpoint, Path(yaml_file).parent)
        if coll_name not in collection_mapping:
            print(f"Collection name '{coll_name}' not found in collection mapping for parent. Skipping.")
            continue
        parent_coll_id = collection_mapping[coll_name]
        parent_result = create_document_with_session(session, project_id, database_id, parent_coll_id, data, endpoint)
        if parent_result:
                # Verify by retrieving the document back using its document ID
                get_document_with_session(session, project_id, database_id, parent_coll_id, parent_result['$id'], endpoint)
    print("--- Relationship documents creation complete ---")

# --- Storage/Media Upload Functions ---

def check_bucket_with_session(session, project_id, bucket_id, endpoint):
    """Check if a storage bucket exists and is accessible"""
    print(f"Checking bucket (ID: {bucket_id})...")
    
    bucket_url = f"{endpoint}/storage/buckets/{bucket_id}"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    response = session.get(bucket_url, headers=headers)
    
    if response.status_code == 200:
        bucket = response.json()
        print(f"✅ Bucket found: '{bucket['name']}' (ID: {bucket['$id']})")
        return True
    else:
        print(f"❌ Bucket access failed: {response.text}")
        return False

def get_supported_image_extensions():
    """Get list of supported image file extensions"""
    return ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico']

def get_supported_video_extensions():
    """Get list of supported video file extensions"""
    return ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp', '.ogv']

def get_supported_media_extensions():
    """Get list of all supported media file extensions (images + videos)"""
    return get_supported_image_extensions() + get_supported_video_extensions()

def get_bucket_file_names(session, project_id, bucket_id, endpoint):
    """Get a set of all file names in the bucket for duplicate checking with full pagination support"""
    
    url = f"{endpoint}/storage/buckets/{bucket_id}/files"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    all_files = []
    limit = 100  # Maximum allowed by Appwrite
    
    print("Scanning bucket for existing files...")
    page = 1
    
    while True:
        # Build parameters for current page - use simple limit/offset
        params = {
            'limit': limit,
            'offset': (page - 1) * limit
        }
        
        response = session.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to list files on page {page}: {response.text}")
            # Return what we have so far rather than failing completely
            break
        
        files_data = response.json()
        # Try both 'documents' and 'files' keys for compatibility
        files = files_data.get('files', files_data.get('documents', []))
        total = files_data.get('total', len(all_files))
        
        if not files:
            break
        
        all_files.extend(files)
        print(f"📄 Scanned page {page}: {len(files)} files (Total so far: {len(all_files)}/{total})")
        
        # If we got less than the limit, we've reached the end
        if len(files) < limit:
            break
            
        page += 1
    
    # Return set of file names for fast lookup
    file_names = {file['name'] for file in all_files}
    print(f"✅ Complete scan finished: Found {len(file_names)} existing files across {page} pages")
    return file_names

def get_all_bucket_files_detailed(session, project_id, bucket_id, endpoint):
    """Get detailed information about all files in the bucket with full pagination support"""
    
    url = f"{endpoint}/storage/buckets/{bucket_id}/files"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    all_files = []
    limit = 100  # Maximum allowed by Appwrite
    
    print("Retrieving detailed file information...")
    page = 1
    
    while True:
        # Build parameters for current page - use simple limit/offset
        params = {
            'limit': limit,
            'offset': (page - 1) * limit
        }
        
        response = session.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to retrieve files on page {page}: {response.text}")
            break
        
        files_data = response.json()
        # Try both 'documents' and 'files' keys for compatibility
        files = files_data.get('files', files_data.get('documents', []))
        total = files_data.get('total', len(all_files))
        
        if not files:
            break
        
        all_files.extend(files)
        print(f"📄 Retrieved page {page}: {len(files)} files (Total: {len(all_files)}/{total})")
        
        # If we got less than the limit, we've reached the end
        if len(files) < limit:
            break
            
        page += 1
    
    print(f"✅ Retrieved {len(all_files)} files total across {page} pages")
    return all_files

def find_file_by_name_paginated(session, project_id, bucket_id, file_name, endpoint):
    """Find a specific file by name using paginated search across all pages"""
    
    url = f"{endpoint}/storage/buckets/{bucket_id}/files"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    # First try using Appwrite's search functionality if available
    params = {
        'search': file_name,
        'limit': 100
    }
    
    response = session.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        files_data = response.json()
        # Try both 'documents' and 'files' keys for compatibility
        files = files_data.get('files', files_data.get('documents', []))
        
        # Look for exact match in search results
        for file in files:
            if file['name'] == file_name:
                return file
    
    # If search didn't work or didn't find exact match, fall back to full pagination
    print(f"🔍 Searching for '{file_name}' across all pages...")
    
    all_files = []
    limit = 100
    page = 1
    
    while True:
        # Build parameters for current page - use simple limit/offset
        params = {
            'limit': limit,
            'offset': (page - 1) * limit
        }
        
        response = session.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to search on page {page}: {response.text}")
            break
        
        files_data = response.json()
        # Try both 'documents' and 'files' keys for compatibility
        files = files_data.get('files', files_data.get('documents', []))
        
        if not files:
            break
        
        # Check each file on this page
        for file in files:
            if file['name'] == file_name:
                print(f"✅ Found '{file_name}' on page {page}")
                return file
        
        all_files.extend(files)
        
        # If we got less than the limit, we've reached the end
        if len(files) < limit:
            break
            
        page += 1
    
    print(f"❌ File '{file_name}' not found after searching {page} pages")
    return None

def delete_file_by_name_paginated(session, project_id, bucket_id, file_name, endpoint):
    """Delete a file from bucket by its name using paginated search"""
    
    # Find the file first
    target_file = find_file_by_name_paginated(session, project_id, bucket_id, file_name, endpoint)
    
    if not target_file:
        print(f"❌ File not found for deletion: {file_name}")
        return False
    
    # Delete the file using its ID
    delete_url = f"{endpoint}/storage/buckets/{bucket_id}/files/{target_file['$id']}"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    delete_response = session.delete(delete_url, headers=headers)
    
    if delete_response.status_code == 204:
        print(f"🗑️  Deleted existing file: {file_name} (ID: {target_file['$id']})")
        return True
    else:
        print(f"❌ Failed to delete file {file_name}: {delete_response.text}")
        return False

def upload_file_to_bucket_with_duplicate_check(session, project_id, bucket_id, file_path, endpoint, file_id=None, permissions=None, skip_duplicates=True, overwrite=False, existing_files=None):
    """Upload a single file to Appwrite Storage bucket with duplicate checking"""
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    # Check for duplicates if existing_files set is provided
    if existing_files is not None and file_path.name in existing_files:
        if skip_duplicates and not overwrite:
            print(f"⏭️  Skipping duplicate: {file_path.name} (already exists in bucket)")
            return {'skipped': True, 'file_name': file_path.name, 'reason': 'duplicate'}
        elif overwrite:
            print(f"🔄 Overwriting existing file: {file_path.name}")
            # For overwrite, we'll delete the existing file first
            if not delete_file_by_name_paginated(session, project_id, bucket_id, file_path.name, endpoint):
                print(f"❌ Failed to delete existing file for overwrite: {file_path.name}")
                return None
            # Remove from existing_files set since we're deleting it
            existing_files.discard(file_path.name)
    
    # Generate file ID if not provided
    if not file_id:
        file_id = "unique()"
    
    # Detect MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    url = f"{endpoint}/storage/buckets/{bucket_id}/files"
    headers = {
        "X-Appwrite-Project": project_id
    }
    
    # Prepare the multipart form data
    files = {
        'file': (file_path.name, open(file_path, 'rb'), mime_type)
    }
    
    data = {
        'fileId': file_id
    }
    
    # Add permissions if provided
    if permissions:
        data['permissions'] = json.dumps(permissions)
    
    try:
        response = session.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Uploaded: {file_path.name} -> ID: {result['$id']}")
            # Add to existing_files set to track new uploads
            if existing_files is not None:
                existing_files.add(file_path.name)
            return result
        else:
            print(f"❌ Failed to upload {file_path.name}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading {file_path.name}: {str(e)}")
        return None
    finally:
        # Close the file
        if 'file' in files:
            files['file'][1].close()

def delete_file_by_name(session, project_id, bucket_id, file_name, endpoint):
    """Delete a file from bucket by its name (legacy function - use delete_file_by_name_paginated for better results)"""
    return delete_file_by_name_paginated(session, project_id, bucket_id, file_name, endpoint)

def bulk_upload_media_from_folder(session, project_id, bucket_id, folder_path, endpoint, permissions=None, extensions=None, media_type="images", skip_duplicates=True, overwrite=False):
    """Upload all media files (images/videos) from a folder to Appwrite Storage bucket with duplicate checking"""
    
    folder_path = Path(folder_path)
    
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"❌ Folder not found or not a directory: {folder_path}")
        return []
    
    # Use appropriate default extensions based on media type
    if not extensions:
        if media_type == "videos":
            extensions = get_supported_video_extensions()
        elif media_type == "all" or media_type == "media":
            extensions = get_supported_media_extensions()
        else:  # default to images
            extensions = get_supported_image_extensions()
    
    # Convert extensions to lowercase for comparison
    extensions = [ext.lower() for ext in extensions]
    
    # Find all media files in the folder
    media_files = []
    for ext in extensions:
        media_files.extend(folder_path.glob(f"*{ext}"))
        media_files.extend(folder_path.glob(f"*{ext.upper()}"))
    
    if not media_files:
        print(f"❌ No {media_type} files found in {folder_path}")
        return []
    
    print(f"Found {len(media_files)} {media_type} files to upload...")
    
    # Get existing files for duplicate checking if enabled
    existing_files = None
    if skip_duplicates or overwrite:
        print("Checking for existing files in bucket...")
        existing_files = get_bucket_file_names(session, project_id, bucket_id, endpoint)
    
    successful_uploads = []
    failed_uploads = []
    skipped_duplicates = []
    
    for i, media_file in enumerate(media_files, 1):
        file_size = media_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"Processing {i}/{len(media_files)}: {media_file.name} ({file_size_mb:.2f} MB)")
        
        result = upload_file_to_bucket_with_duplicate_check(
            session, 
            project_id, 
            bucket_id, 
            media_file, 
            endpoint, 
            permissions=permissions,
            skip_duplicates=skip_duplicates,
            overwrite=overwrite,
            existing_files=existing_files
        )
        
        if result:
            if result.get('skipped'):
                skipped_duplicates.append({
                    'file_name': media_file.name,
                    'reason': result.get('reason', 'duplicate')
                })
            else:
                successful_uploads.append({
                    'file_name': media_file.name,
                    'file_id': result['$id'],
                    'file_path': str(media_file),
                    'size': result.get('sizeOriginal', 0),
                    'mime_type': result.get('mimeType', ''),
                    'file_type': 'video' if media_file.suffix.lower() in get_supported_video_extensions() else 'image'
                })
        else:
            failed_uploads.append(str(media_file))
        
        # Longer delay for video files to avoid rate limiting
        delay = 0.5 if media_file.suffix.lower() in get_supported_video_extensions() else 0.1
        time.sleep(delay)
    
    # Print comprehensive summary
    print("\n--- Upload Summary ---")
    print(f"Total files found: {len(media_files)}")
    print(f"Successfully uploaded: {len(successful_uploads)}")
    print(f"Skipped duplicates: {len(skipped_duplicates)}")
    print(f"Failed uploads: {len(failed_uploads)}")
    
    # Categorize by type
    images = [f for f in successful_uploads if f['file_type'] == 'image']
    videos = [f for f in successful_uploads if f['file_type'] == 'video']
    
    if images:
        print(f"\n✅ Successfully uploaded {len(images)} images:")
        for upload in images:
            size_mb = upload['size'] / (1024 * 1024)
            print(f"  - {upload['file_name']} (ID: {upload['file_id']}, Size: {size_mb:.2f} MB)")
    
    if videos:
        print(f"\n✅ Successfully uploaded {len(videos)} videos:")
        for upload in videos:
            size_mb = upload['size'] / (1024 * 1024)
            print(f"  - {upload['file_name']} (ID: {upload['file_id']}, Size: {size_mb:.2f} MB)")
    
    if skipped_duplicates:
        print(f"\n⏭️  Skipped {len(skipped_duplicates)} duplicate files:")
        for skipped in skipped_duplicates:
            print(f"  - {skipped['file_name']} ({skipped['reason']})")
    
    if failed_uploads:
        print("\n❌ Failed uploads:")
        for failed_file in failed_uploads:
            print(f"  - {failed_file}")

    return successful_uploads

def bulk_upload_files_from_folder(session, project_id, bucket_id, folder_path, endpoint, permissions=None,
                                  skip_duplicates=True, overwrite=False):
    """Upload all files from a folder to Appwrite Storage bucket."""

    folder_path = Path(folder_path)

    if not folder_path.exists() or not folder_path.is_dir():
        print(f"❌ Folder not found or not a directory: {folder_path}")
        return []

    all_files = [f for f in folder_path.iterdir() if f.is_file()]

    if not all_files:
        print(f"❌ No files found in {folder_path}")
        return []

    print(f"Found {len(all_files)} files to upload...")

    existing_files = None
    if skip_duplicates or overwrite:
        print("Checking for existing files in bucket...")
        existing_files = get_bucket_file_names(session, project_id, bucket_id, endpoint)

    successful_uploads = []
    failed_uploads = []
    skipped_duplicates = []

    for i, file_path in enumerate(all_files, 1):
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        print(f"Processing {i}/{len(all_files)}: {file_path.name} ({file_size_mb:.2f} MB)")

        result = upload_file_to_bucket_with_duplicate_check(
            session,
            project_id,
            bucket_id,
            file_path,
            endpoint,
            permissions=permissions,
            skip_duplicates=skip_duplicates,
            overwrite=overwrite,
            existing_files=existing_files
        )

        if result:
            if result.get('skipped'):
                skipped_duplicates.append({
                    'file_name': file_path.name,
                    'reason': result.get('reason', 'duplicate')
                })
            else:
                successful_uploads.append({
                    'file_name': file_path.name,
                    'file_id': result['$id'],
                    'file_path': str(file_path),
                    'size': result.get('sizeOriginal', 0),
                    'mime_type': result.get('mimeType', '')
                })
        else:
            failed_uploads.append(str(file_path))

        time.sleep(0.1)

    print("\n--- Upload Summary ---")
    print(f"Total files found: {len(all_files)}")
    print(f"Successfully uploaded: {len(successful_uploads)}")
    print(f"Skipped duplicates: {len(skipped_duplicates)}")
    print(f"Failed uploads: {len(failed_uploads)}")

    if skipped_duplicates:
        print(f"\n⏭️  Skipped {len(skipped_duplicates)} duplicate files:")
        for skipped in skipped_duplicates:
            print(f"  - {skipped['file_name']} ({skipped['reason']})")

    if failed_uploads:
        print("\n❌ Failed uploads:")
        for failed_file in failed_uploads:
            print(f"  - {failed_file}")

    return successful_uploads

def list_bucket_files(session, project_id, bucket_id, endpoint):
    """List all files in a storage bucket with full pagination support"""
    
    files = get_all_bucket_files_detailed(session, project_id, bucket_id, endpoint)
    
    if files:
        print(f"✅ Found {len(files)} total files in bucket {bucket_id}")
        
        print("\n--- Files in Bucket ---")
        for i, file in enumerate(files, 1):
            size_mb = file.get('sizeOriginal', 0) / (1024 * 1024)
            print(f"{i}. ID: {file['$id']}")
            print(f"   Name: {file['name']}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   MIME Type: {file.get('mimeType', 'unknown')}")
            print(f"   Created: {file['$createdAt']}")
            print("-" * 40)
        
        return files
    else:
        print(f"❌ No files found or failed to retrieve files from bucket {bucket_id}")
        return []

def generate_team_permissions(team_id):
    """
    Generate basic permission strings for a team with the given team_id.
    
    These permissions can be used when creating documents or setting access controls.
    
    :param team_id: The team ID to incorporate into the permission strings.
    :return: A list of permission strings.
    """
    return [
        f"role:team:{team_id}.read",
        f"role:team:{team_id}.update",
        f"role:team:{team_id}.delete"
    ]

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk create documents in Appwrite from YAML data and upload images")
    parser.add_argument("--yaml-file", help="Path to YAML file containing document data")
    parser.add_argument("--email", help="Appwrite login email")
    parser.add_argument("--password", help="Appwrite login password")
    parser.add_argument("--project-id", help="Appwrite project ID")
    parser.add_argument("--database-id", help="Appwrite database ID")
    parser.add_argument("--collection-id", help="Appwrite collection ID")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification")
    
    # Storage/Image upload arguments
    parser.add_argument("--bucket-id", help="Appwrite storage bucket ID")
    parser.add_argument("--media-folder", help="Path to folder containing media files to upload")
    parser.add_argument("--images-folder", help="Path to folder containing images to upload (legacy)")
    parser.add_argument("--upload-media", action="store_true", help="Upload media files from specified folder to bucket")
    parser.add_argument("--upload-files", action="store_true", help="Upload all files from specified folder to bucket")
    parser.add_argument("--upload-images", action="store_true", help="Upload images from specified folder to bucket (legacy)")
    parser.add_argument("--upload-videos", action="store_true", help="Upload videos from specified folder to bucket")
    parser.add_argument("--media-type", choices=["images", "videos", "all"], default="images", 
                        help="Type of media to upload (images, videos, or all)")
    parser.add_argument("--check-bucket", action="store_true", help="Check if storage bucket exists")
    parser.add_argument("--list-files", action="store_true", help="List files in storage bucket")
    parser.add_argument("--media-extensions", nargs="+", help="Supported media extensions (default: auto-detect by type)")
    parser.add_argument("--image-extensions", nargs="+", help="Supported image extensions (legacy)")
    parser.add_argument("--video-extensions", nargs="+", help="Supported video extensions")
    parser.add_argument("--file-permissions", help="JSON string of file permissions for uploaded files")
    parser.add_argument("--skip-duplicates", action="store_true", default=True, help="Skip files that already exist in bucket (default: True)")
    parser.add_argument("--no-skip-duplicates", action="store_true", help="Upload all files even if duplicates exist")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files with same name")
    
    # Test arguments
    parser.add_argument("--test-connection", action="store_true", help="Test connection to Appwrite")
    parser.add_argument("--check-database", action="store_true", help="Check if database exists")
    parser.add_argument("--check-collection", action="store_true", help="Check if collection exists")
    parser.add_argument("--list-documents", action="store_true", help="List documents from a collection")
    parser.add_argument("--create-document", action="store_true", help="Create a single document from the first YAML entry")
    parser.add_argument("--relations", action="store_true", help="Process YAML file with Children/Parent relationships")

    args = parser.parse_args()
    
    # Get credentials
    email = args.email or os.environ.get("APPWRITE_EMAIL")
    password = args.password or os.environ.get("APPWRITE_PASSWORD")
    project_id = args.project_id or os.environ.get("APPWRITE_PROJECT_ID")
    endpoint = os.environ.get("APPWRITE_API_ENDPOINT")
    
    if not email or not password or not project_id:
        print("Error: Missing credentials. Provide --email, --password, and --project-id or set them in .env/environment variables.")
        sys.exit(1)
    
    # Create client
    session = create_session(
        email=email,
        password=password,
        project_id=project_id,
        endpoint=endpoint,
        verify_ssl=not args.no_verify_ssl
    )
    
    if not session:
        sys.exit(1)
    
    # Handle test options using the session
    if args.test_connection:
        if test_connection_with_session(session, project_id, endpoint):
            sys.exit(0)
        else:
            sys.exit(1)

    if args.check_database:
        if not args.database_id:
            print("Error: Database ID not provided. Use --database-id.")
            sys.exit(1)
        if check_database_with_session(session, project_id, args.database_id, endpoint):
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle storage bucket check
    if args.check_bucket:
        if not args.bucket_id:
            print("Error: Bucket ID not provided. Use --bucket-id.")
            sys.exit(1)
        if check_bucket_with_session(session, project_id, args.bucket_id, endpoint):
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle file listing in bucket
    if args.list_files:
        if not args.bucket_id:
            print("Error: Bucket ID not provided. Use --bucket-id.")
            sys.exit(1)

        files = list_bucket_files(session, project_id, args.bucket_id, endpoint)
        sys.exit(0 if files is not None else 1)

    # Handle generic file upload
    if args.upload_files:
        folder_path = args.media_folder
        if not folder_path:
            print("Error: Need --media-folder for file upload")
            sys.exit(1)

        if not args.bucket_id:
            print("Error: Need --bucket-id for file upload")
            sys.exit(1)

        permissions = None
        if args.file_permissions:
            try:
                permissions = json.loads(args.file_permissions)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for --file-permissions")
                sys.exit(1)

        skip_duplicates = not args.no_skip_duplicates
        overwrite = args.overwrite

        if skip_duplicates and overwrite:
            print("Error: Cannot use both --skip-duplicates and --overwrite. Choose one approach.")
            sys.exit(1)

        successful_uploads = bulk_upload_files_from_folder(
            session,
            project_id,
            args.bucket_id,
            folder_path,
            endpoint,
            permissions=permissions,
            skip_duplicates=skip_duplicates,
            overwrite=overwrite
        )

        sys.exit(0 if successful_uploads else 1)

    # Handle media upload (new unified approach)
    if args.upload_media or args.upload_videos:
        folder_path = args.media_folder
        if not folder_path:
            print("Error: Need --media-folder for media upload")
            sys.exit(1)
        
        if not args.bucket_id:
            print("Error: Need --bucket-id for media upload")
            sys.exit(1)
        
        # Determine media type
        if args.upload_videos:
            media_type = "videos"
        else:
            media_type = args.media_type
        
        # Parse permissions if provided
        permissions = None
        if args.file_permissions:
            try:
                permissions = json.loads(args.file_permissions)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for --file-permissions")
                sys.exit(1)
        
        # Determine duplicate handling
        skip_duplicates = not args.no_skip_duplicates  # Default is True unless explicitly disabled
        overwrite = args.overwrite
        
        # Validate conflicting options
        if skip_duplicates and overwrite:
            print("Error: Cannot use both --skip-duplicates and --overwrite. Choose one approach.")
            sys.exit(1)
        
        # Use custom extensions if provided
        extensions = None
        if args.media_extensions:
            extensions = args.media_extensions
        elif args.video_extensions and media_type == "videos":
            extensions = args.video_extensions
        
        successful_uploads = bulk_upload_media_from_folder(
            session,
            project_id,
            args.bucket_id,
            folder_path,
            endpoint,
            permissions=permissions,
            extensions=extensions,
            media_type=media_type,
            skip_duplicates=skip_duplicates,
            overwrite=overwrite
        )
        
        sys.exit(0 if successful_uploads else 1)

    # Handle legacy image upload
    if args.upload_images:
        folder_path = args.images_folder or args.media_folder
        if not folder_path:
            print("Error: Need --images-folder or --media-folder for image upload")
            sys.exit(1)
        
        if not args.bucket_id:
            print("Error: Need --bucket-id for image upload")
            sys.exit(1)
        
        # Parse permissions if provided
        permissions = None
        if args.file_permissions:
            try:
                permissions = json.loads(args.file_permissions)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for --file-permissions")
                sys.exit(1)
        
        # Determine duplicate handling
        skip_duplicates = not args.no_skip_duplicates  # Default is True unless explicitly disabled
        overwrite = args.overwrite
        
        # Validate conflicting options
        if skip_duplicates and overwrite:
            print("Error: Cannot use both --skip-duplicates and --overwrite. Choose one approach.")
            sys.exit(1)
        
        # Use custom extensions if provided
        extensions = args.image_extensions if args.image_extensions else None
        
        successful_uploads = bulk_upload_media_from_folder(
            session,
            project_id,
            args.bucket_id,
            folder_path,
            endpoint,
            permissions=permissions,
            extensions=extensions,
            media_type="images",
            skip_duplicates=skip_duplicates,
            overwrite=overwrite
        )
        
        sys.exit(0 if successful_uploads else 1)

    # Add check_collection functionality if needed
    if args.check_collection:
        if not args.database_id or not args.collection_id:
            print("Error: Need both --database-id and --collection-id for checking collection")
            sys.exit(1)
        
        collection_url = f"{endpoint}/databases/{args.database_id}/collections/{args.collection_id}"
        headers = {"X-Appwrite-Project": project_id}
        
        response = session.get(collection_url, headers=headers)
        
        if response.status_code == 200:
            collection = response.json()
            print(f"✅ Collection found: '{collection['name']}' (ID: {collection['$id']})")
            sys.exit(0)
        else:
            print(f"❌ Collection not found or access denied: {response.text}")
            sys.exit(1)

    # Handle document listing with session
    if args.list_documents:
        if not args.database_id or not args.collection_id:
            print("Error: Need both --database-id and --collection-id for listing documents")
            sys.exit(1)
        
        documents = get_collection_documents_with_session(
            session,
            project_id,
            args.database_id,
            args.collection_id,
            endpoint
        )
        
        if documents:
            print("\n--- Document List ---")
            for doc in documents['documents']:
                print(f"ID: {doc['$id']}")
                print(f"Created: {doc['$createdAt']}")
                # Print a few key fields from each document
                for key, value in doc.items():
                    if not key.startswith('$') and not isinstance(value, dict) and not isinstance(value, list):
                        print(f"{key}: {value}")
                print("-" * 30)
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Handle create single document with session
    if args.create_document:
        if not all([args.yaml_file, args.database_id, args.collection_id]):
            print("Error: Need --yaml-file, --database-id, and --collection-id for creating a document")
            sys.exit(1)
        
        # Load only the first item from the YAML file
        data = load_yaml_data(args.yaml_file)
        if not data or len(data) == 0:
            print("Error: No data found in YAML file")
            sys.exit(1)
        
        result = create_document_with_session(
            session, 
            project_id, 
            args.database_id, 
            args.collection_id, 
            data[0],  # Use the first item only
            endpoint
        )
        
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Process YAML for relationships if --relations flag is provided
    if args.yaml_file and args.relations:
        # Update the collection mapping here based on your Appwrite project
        collection_mapping = {
            "Country": "67e93ec5002b9487fffa",
            "Space": "67e93f0e003422c142d2",
            "TimelineNode": "67e94422000de551b64a",
            "nezuko": "67fbb8b30015f0e807c6",
            "Properties": "67f2ac3000218cb04d4e",
            "InvestmentStrategy": "67e94032001f3cdd2781",
            "Neighbourhood": "67e941e5003bd086de54",
            "InvestmentStrategy": "67e94032001f3cdd2781",
            "InvestmentStrategyHighlights": "67e940800002fb4d894a",
        }
        create_documents_with_relationships(
            session,
            args.yaml_file,
            project_id,
            args.database_id,
            collection_mapping,
            endpoint,
            bucket_id=args.bucket_id,
        )
        sys.exit(0)    

    # Handle bulk document creation with session
    if args.yaml_file and args.database_id and args.collection_id and not args.create_document:
        bulk_create_documents_with_session(
            session,
            args.yaml_file,
            project_id,
            args.database_id,
            args.collection_id,
            endpoint
        )
        sys.exit(0)