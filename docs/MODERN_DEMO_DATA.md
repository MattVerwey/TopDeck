# Modernized Demo Data

TopDeck now includes **modernized demo data** with fun, memorable resource names instead of generic ones!

## 🍰 What's New?

Instead of boring names like `aks-demo-prod` and `appgw-demo`, we now have engaging names that are:
- **Memorable**: Easy to remember and discuss
- **Fun**: Makes demos and testing more enjoyable
- **Professional**: Still maintains appropriate naming conventions
- **Diverse**: Covers various types of resources

## 📦 Demo Resources

### Kubernetes Cluster
- **sweet-treats-cluster**: Main AKS cluster hosting all bakery applications

### Namespaces
- **chocolate-factory**: Frontend web applications
- **bakery-api**: Backend API microservices
- **sweet-storage**: Data tier with databases and caches

### Applications (Pods)
- **chocolate-cookie-api**: Chocolate cookie recipe API service
  - Image: `acr.io/chocolate-api:v2.1`
  - Replicas: 3
  - Purpose: Recipe management and cookie data

- **victoria-sponge-web**: Victoria sponge cake ordering frontend
  - Image: `acr.io/victoria-web:v1.8`
  - Replicas: 2
  - Purpose: Customer-facing web interface

- **rainbow-cupcake-processor**: Rainbow cupcake order processing
  - Image: `acr.io/cupcake-processor:v3.0`
  - Replicas: 4
  - Purpose: Order fulfillment and processing

- **butter-cream-cache**: Redis cache for recipe data
  - Image: `redis:7.0`
  - Replicas: 1
  - Purpose: High-performance caching layer

### Databases
- **victoria-sponge-db**: PostgreSQL database
  - Type: PostgreSQL
  - Purpose: Recipe and order data storage

- **cookie-inventory-db**: Cosmos DB instance
  - Type: Cosmos DB
  - Purpose: Cookie inventory and stock tracking

### Networking
- **sweet-gateway**: Application Gateway
  - SKU: WAF_v2
  - Public IP: 20.1.2.3
  - Purpose: Internet-facing load balancer

### Storage
- **sweetimages001**: Storage Account
  - Type: Standard_LRS
  - Containers: `product-images`, `recipe-photos`
  - Purpose: Product and recipe image storage

## 🔗 Relationships

The demo data includes realistic relationships between resources:

```
sweet-gateway (Application Gateway)
    └─ ROUTES_TO → sweet-treats-cluster (AKS)
        └─ CONTAINS → chocolate-factory (Namespace)
            └─ CONTAINS → victoria-sponge-web (Pod)
                └─ ACCESSES → sweetimages001 (Storage)

sweet-treats-cluster (AKS)
    └─ CONTAINS → bakery-api (Namespace)
        ├─ CONTAINS → chocolate-cookie-api (Pod)
        │   ├─ DEPENDS_ON → victoria-sponge-db (Database)
        │   └─ USES → butter-cream-cache (Pod)
        │
        └─ CONTAINS → rainbow-cupcake-processor (Pod)
            └─ DEPENDS_ON → cookie-inventory-db (Database)
```

## 🚀 How to Use

### Create the Demo Data

Run the modern demo data script:

```bash
# Make sure Neo4j is running
docker-compose up -d neo4j

# Run the demo data script
python scripts/modern_demo_data.py
```

### View in Neo4j Browser

Open Neo4j Browser at http://localhost:7474 and run:

```cypher
// View all demo resources
MATCH (n) WHERE n.demo = true
RETURN n
LIMIT 50

// View relationships
MATCH path = (n)-[r]->(m)
WHERE n.demo = true AND m.demo = true
RETURN path
LIMIT 50

// Find the chocolate cookie API
MATCH (pod:Pod {name: 'chocolate-cookie-api'})
RETURN pod

// See what chocolate-cookie-api depends on
MATCH (api:Pod {name: 'chocolate-cookie-api'})
      -[r:DEPENDS_ON|USES]->
      (dep)
RETURN api, r, dep
```

### Clear Demo Data

The script automatically clears existing demo data before creating new data. To manually clear:

```cypher
MATCH (n) WHERE n.demo = true
DETACH DELETE n
```

## 💡 Why These Names?

The names follow a **bakery/sweets theme** which:

1. **Makes testing more fun**: "Let's debug the chocolate-cookie-api" is more engaging than "Let's debug service-a"
2. **Easy to remember**: Unique names are easier to recall in conversations
3. **Professional yet playful**: Maintains professionalism while being memorable
4. **Consistent theming**: All names follow the same theme for coherence
5. **Real-world analogues**: Represents real microservice patterns (API, web, processor, cache)

## 🎯 Use Cases

This demo data is perfect for:

- **Training**: Teaching new users how TopDeck works
- **Development**: Testing new features with realistic data
- **Demos**: Showing TopDeck to stakeholders
- **Testing**: Verifying topology and risk analysis features
- **Documentation**: Creating screenshots and examples

## 🔄 Customization

Want to create your own themed demo data? The script is easy to customize:

1. Copy `scripts/modern_demo_data.py` to a new file
2. Update the resource names to your theme
3. Modify relationships as needed
4. Run your custom script

Example themes you could use:
- **Space theme**: `mars-rover-api`, `jupiter-gateway`, `saturn-db`
- **Ocean theme**: `coral-reef-api`, `deep-blue-cache`, `pacific-db`
- **City theme**: `broadway-web`, `times-square-api`, `central-park-db`
- **Music theme**: `jazz-api`, `blues-gateway`, `rock-db`

## 📝 Technical Details

The demo data script (`scripts/modern_demo_data.py`):
- Connects to Neo4j at `bolt://localhost:7687`
- Creates nodes with `demo: true` property for easy cleanup
- Establishes realistic relationships between resources
- Includes proper resource properties (region, subscription, etc.)
- Uses proper Azure resource ID format

All demo resources:
- Have `demo: true` flag
- Use subscription ID: `12345678-1234-1234-1234-123456789abc`
- Use resource group: `rg-bakery-prod`
- Are in region: `eastus`
- Have realistic properties and configurations

Enjoy your modernized, fun demo data! 🎉
