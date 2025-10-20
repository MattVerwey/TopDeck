# Issue: Azure Resource Discovery Failing Due to Complex Properties in Neo4j Storage

## Problem Description

Azure resource discovery is successfully finding 614 resources but failing to store them in Neo4j due to complex property types in Azure resource tags and properties. Neo4j only accepts primitive types (strings, numbers, booleans) and arrays thereof, but Azure resources contain complex nested objects.

## Error Details

**Error Message Pattern:**
```
❌ Failed to store [resource-name]: {code: Neo.ClientError.Statement.TypeError} {message: Property values can only be of primitive types or arrays thereof. Encountered: Map{Product Name -> String("..."), Value Stream -> String("...")}.}
```

**Example Failing Resources:**
- `sisexternalaksdata000001`: Contains `Map{Product Name -> "Azure Kubernetes Service", Value Stream -> "Shared"}`
- `editor-dev-uks-as`: Contains complex nested objects with creation dates, owners, service details, etc.

## Root Cause Analysis

1. **Azure API Returns Complex Objects**: Azure Resource Manager API returns resource tags and properties as nested dictionaries/maps
2. **Insufficient Data Flattening**: While we attempted to flatten complex objects in the Azure mapper, the data is still reaching Neo4j as complex types
3. **Multiple Conversion Points**: Data passes through several conversion layers:
   - Azure SDK → Azure Mapper → DiscoveredResource → `to_neo4j_properties()` → Neo4j storage

## Current Status

- ✅ **Discovery Working**: Successfully discovering 614 Azure resources
- ✅ **API Endpoints Working**: Backend API returning data correctly
- ✅ **Frontend Configuration**: React frontend properly configured
- ❌ **Data Storage**: Zero resources successfully stored in Neo4j
- ❌ **Real Data Display**: Frontend only shows sample data, not real Azure infrastructure

## Impact

- Users cannot see their actual Azure infrastructure topology
- TopDeck frontend displays empty/sample data instead of real discovered resources
- Discovery process appears successful but provides no value to end users

## Technical Details

**Affected Files:**
- `src/topdeck/discovery/azure/mapper.py` - Azure resource mapping logic
- `src/topdeck/discovery/models.py` - `DiscoveredResource.to_neo4j_properties()` method
- `examples/multi_cloud_discovery.py` - Discovery execution script

**Failed Attempts:**
1. Added tag flattening logic in Azure mapper
2. Added property flattening logic in Azure mapper  
3. Enhanced `to_neo4j_properties()` method to flatten both tags and properties

**Sample Complex Data Structure:**
```python
{
    "Product Name": "Azure Kubernetes Service",
    "Value Stream": "Shared",
    "runningPattern": "officeHours",
    "dates": {
        "creationDate": "2025-09-10T09:05:19Z",
        "reviewDate": "2025-10-10T09:05:19Z"
    },
    "owners": {
        "businessOwner": "user@company.com",
        "technicalOwner": "dev@company.com"
    }
}
```

## Proposed Solution

Need to implement comprehensive data flattening that:
1. **Recursively Flattens**: Handle deeply nested objects and arrays
2. **JSON Serialization**: Convert complex objects to JSON strings for Neo4j compatibility
3. **Type Safety**: Ensure all values are primitive types before Neo4j storage
4. **Preserves Information**: Maintain original data structure in JSON format for later parsing

## Steps to Reproduce

1. Set up Azure authentication with valid service principal
2. Run `python examples/multi_cloud_discovery.py`
3. Observe: Resources discovered but storage failures
4. Check Neo4j database: Zero nodes stored
5. Check frontend: Only sample data visible

## Environment

- **Python Version**: 3.x
- **Neo4j Version**: Running in Docker
- **Azure SDK**: Latest version
- **Discovery Count**: 614 Azure resources found
- **Storage Success Rate**: 0%

## Expected Behavior

- All 614 discovered Azure resources should be successfully stored in Neo4j
- Frontend should display real Azure infrastructure topology
- Complex Azure properties should be stored as JSON strings in Neo4j
- Real-time infrastructure visibility should be available to users

## Acceptance Criteria

- [ ] All Azure resources store successfully in Neo4j (0 failures)
- [ ] Neo4j database contains 614+ resource nodes
- [ ] Frontend displays real Azure infrastructure data
- [ ] Complex properties preserved as JSON strings
- [ ] API endpoints return real resource data instead of samples