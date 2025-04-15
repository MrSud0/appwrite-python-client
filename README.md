# Appwrite Client Tool

A Python-based command-line tool for interacting with Appwrite databases and collections. This tool allows you to manage documents, test connections, and work with relationships within your Appwrite backend.

## Features

- Authentication with Appwrite using email/password
- Test connectivity to your Appwrite instance
- Check database and collection access
- Create, update, and delete documents
- Bulk import documents from YAML files
- Create documents with relationships
- Team management functionality
- Support for SSL verification toggle

## Prerequisites

- Python 3.6+
- An Appwrite account and project
- Required Python packages (see Installation)

## Installation

1. Clone this repository or download the script
2. Install required dependencies:

```bash
pip install requests pyyaml python-dotenv
```

3. Create a `.env` file in the same directory with your Appwrite credentials:

```
APPWRITE_EMAIL=your-email@example.com
APPWRITE_PASSWORD=your-password
APPWRITE_PROJECT_ID=your-project-id
APPWRITE_API_ENDPOINT=https://your-appwrite-instance/v1
```

## Usage

### Basic Connection Testing

Test your connection to Appwrite:

```bash
python appwrite_client.py --test-connection
```

### Working with Databases

Check if a database exists:

```bash
python appwrite_client.py --check-database --database-id=your-database-id
```

### Working with Collections

Check if a collection exists:

```bash
python appwrite_client.py --check-database --database-id=your-database-id --check-collection --collection-id=your-collection-id
```

List documents in a collection:

```bash
python appwrite_client.py --database-id=your-database-id --collection-id=your-collection-id --list-documents
```

### Creating Documents

Create a single document from a YAML file (uses the first entry):

```bash
python appwrite_client.py --yaml-file=your-data.yaml --database-id=your-database-id --collection-id=your-collection-id --create-document
```

Bulk create documents from a YAML file:

```bash
python appwrite_client.py --yaml-file=your-data.yaml --database-id=your-database-id --collection-id=your-collection-id
```

### Working with Relationships

Process YAML file with parent-child relationships:

```bash
python appwrite_client.py --yaml-file=relationships.yaml --database-id=your-database-id --relations
```

The YAML file for relationships should have this structure:

```yaml
Children:
  - collection_name: "CollectionName1"
    data: &child_anchor1
      field1: "value1"
      field2: "value2"
  
  - collection_name: "CollectionName2"
    data: &child_anchor2
      field1: "value1"
      field2: "value2"

Parent:
  - collection_name: "ParentCollection"
    data:
      name: "Parent Name"
      child_ref1:
        value: *child_anchor1
        relation: "oneToOne"
      child_ref2:
        value: *child_anchor2
        relation: "oneToMany"
```

### Team Management

The script includes functions for team management but isn't exposed via command-line arguments. You can use these functions programmatically:

```python
# Create a team
team = create_team(session, project_id, "Team Name", ["admin", "editor"], endpoint)

# Add a user to a team
member = add_user_to_team(session, project_id, team_id, "user@example.com", 
                          ["admin"], "https://yourapp.com/callback", endpoint)
```

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--yaml-file` | Path to YAML file containing document data |
| `--email` | Appwrite login email (overrides .env) |
| `--password` | Appwrite login password (overrides .env) |
| `--project-id` | Appwrite project ID (overrides .env) |
| `--database-id` | Appwrite database ID |
| `--collection-id` | Appwrite collection ID |
| `--no-verify-ssl` | Disable SSL certificate verification |
| `--test-connection` | Test connection to Appwrite |
| `--check-database` | Check if database exists |
| `--check-collection` | Check if collection exists |
| `--list-documents` | List documents from a collection |
| `--create-document` | Create a single document from the first YAML entry |
| `--relations` | Process YAML file with Children/Parent relationships |

## Example YAML for Document Creation

```yaml
- name: "Document 1"
  description: "This is the first document"
  status: "active"
  tags: ["tag1", "tag2"]

- name: "Document 2"
  description: "This is the second document"
  status: "pending"
  tags: ["tag2", "tag3"]
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `APPWRITE_EMAIL` | Your Appwrite account email |
| `APPWRITE_PASSWORD` | Your Appwrite account password |
| `APPWRITE_PROJECT_ID` | Your Appwrite project ID |
| `APPWRITE_API_ENDPOINT` | URL of your Appwrite API (default: https://cloud.appwrite.io/v1) |

## Notes

- When dealing with large datasets, the tool includes rate limiting (0.2s delay) to avoid overloading the Appwrite API
- For security, use `.env` files or environment variables rather than passing credentials via command line

## Error Handling

The tool provides detailed error messages when operations fail. For bulk operations, a summary is displayed showing successful and failed operations.

## Contributing

Feel free to submit issues or pull requests to improve this tool.

## License

This project is licensed under the MIT License.