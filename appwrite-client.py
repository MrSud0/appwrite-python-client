import yaml
import sys
import os
import urllib3
import requests
from dotenv import load_dotenv
import time
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
    """
    Retrieve a document from a specific collection using its documentId.
    """
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
    """
    Retrieve a collection's ID by its name using the Appwrite REST API.
    """
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

def create_documents_with_relationships(session, yaml_file, project_id, database_id, collection_mapping, endpoint):
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
    """
    yaml_data = load_yaml_data(yaml_file)
    if not ("Children" in yaml_data and "Parent" in yaml_data):
        print("YAML file does not contain both 'Children' and 'Parent' sections.")
        return
    
    child_mapping = {}
    print("--- Processing Children ---")
    for child in yaml_data["Children"]:
        coll_name = child.get("collection_name")
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
        if coll_name not in collection_mapping:
            print(f"Collection name '{coll_name}' not found in collection mapping for parent. Skipping.")
            continue
        parent_coll_id = collection_mapping[coll_name]
        parent_result = create_document_with_session(session, project_id, database_id, parent_coll_id, data, endpoint)
        if parent_result:
                # Verify by retrieving the document back using its document ID
                get_document_with_session(session, project_id, database_id, parent_coll_id, parent_result['$id'], endpoint)
    print("--- Relationship documents creation complete ---")

# --- New functions for team management ---

def create_team(session, project_id, name, roles, endpoint"):
    """
    Create a new team with the specified name and roles.
    
    :param session: The authenticated requests session.
    :param project_id: The Appwrite project ID.
    :param name: The name of the team.
    :param roles: A list of roles (strings) for the team. These roles will be used in permission strings.
    :param endpoint: The Appwrite endpoint URL.
    :return: The team object if created successfully, or None.
    """
    url = f"{endpoint}/teams"
    headers = {
        "X-Appwrite-Project": project_id,
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "roles": roles
    }
    response = session.post(url, headers=headers, json=data)
    if response.status_code == 201:
        team = response.json()
        print(f"✅ Team '{name}' created successfully with ID: {team['$id']}")
        return team
    else:
        print(f"❌ Failed to create team '{name}': {response.text}")
        return None

def add_user_to_team(session, project_id, team_id, email, roles, callback_url, endpoint):
    """
    Add a user to an existing team with the given roles.
    
    :param session: The authenticated requests session.
    :param project_id: The Appwrite project ID.
    :param team_id: The ID of the team.
    :param email: The email of the user to add.
    :param roles: A list of roles (strings) to assign to the user within the team.
    :param callback_url: A URL the user will be redirected to after accepting the team invitation.
    :param endpoint: The Appwrite endpoint URL.
    :return: The member object if added successfully, or None.
    """
    url = f"{endpoint}/teams/{team_id}/members"
    headers = {
        "X-Appwrite-Project": project_id,
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "roles": roles,
        "url": callback_url
    }
    response = session.post(url, headers=headers, json=data)
    if response.status_code == 201:
        member = response.json()
        print(f"✅ Member '{email}' added to team with ID: {member['$id']}")
        return member
    else:
        print(f"❌ Failed to add user to team: {response.text}")
        return None

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
    
    parser = argparse.ArgumentParser(description="Bulk create documents in Appwrite from YAML data")
    parser.add_argument("--yaml-file", help="Path to YAML file containing document data")
    parser.add_argument("--email", help="Appwrite login email")
    parser.add_argument("--password", help="Appwrite login password")
    parser.add_argument("--project-id", help="Appwrite project ID")
    parser.add_argument("--database-id", help="Appwrite database ID")
    parser.add_argument("--collection-id", help="Appwrite collection ID")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification")
    
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
    endpoint = args.email or os.environ.get("APPWRITE_API_ENDPOINT")
    
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
            "Properties": "67f2ac3000218cb04d4e"
        }
        create_documents_with_relationships(session, args.yaml_file, project_id, args.database_id, collection_mapping, endpoint)
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