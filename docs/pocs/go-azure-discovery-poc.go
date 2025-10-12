package main

/*
Proof of Concept: Azure Resource Discovery with Go
This POC demonstrates Azure resource discovery using the Azure SDK for Go.
*/

import (
	"context"
	"fmt"
	"strings"
	"sync"
	"time"
)

// AzureResource represents a discovered Azure resource
type AzureResource struct {
	ID            string                 `json:"id"`
	Name          string                 `json:"name"`
	Type          string                 `json:"type"`
	Location      string                 `json:"location"`
	ResourceGroup string                 `json:"resource_group"`
	Properties    map[string]interface{} `json:"properties"`
}

// AzureDiscoveryService handles Azure resource discovery
type AzureDiscoveryService struct {
	subscriptionID string
	// In production: credential would be azidentity.DefaultAzureCredential()
	// resourceClient would be armresources.Client
}

// NewAzureDiscoveryService creates a new discovery service instance
func NewAzureDiscoveryService(subscriptionID string) *AzureDiscoveryService {
	return &AzureDiscoveryService{
		subscriptionID: subscriptionID,
	}
}

// DiscoverAllResources discovers all resources in the subscription concurrently
func (s *AzureDiscoveryService) DiscoverAllResources(ctx context.Context) ([]AzureResource, error) {
	fmt.Printf("🔍 Starting discovery for subscription: %s\n", s.subscriptionID)

	var wg sync.WaitGroup
	resourceChan := make(chan []AzureResource, 6)

	// Launch concurrent goroutines for each resource type
	discoveryFuncs := []func(context.Context) ([]AzureResource, error){
		s.discoverVirtualMachines,
		s.discoverAppServices,
		s.discoverAKSClusters,
		s.discoverSQLDatabases,
		s.discoverStorageAccounts,
		s.discoverLoadBalancers,
	}

	for _, fn := range discoveryFuncs {
		wg.Add(1)
		go func(f func(context.Context) ([]AzureResource, error)) {
			defer wg.Done()
			resources, err := f(ctx)
			if err != nil {
				fmt.Printf("Error during discovery: %v\n", err)
				return
			}
			resourceChan <- resources
		}(fn)
	}

	// Close channel when all goroutines complete
	go func() {
		wg.Wait()
		close(resourceChan)
	}()

	// Collect all resources
	var allResources []AzureResource
	for resources := range resourceChan {
		allResources = append(allResources, resources...)
	}

	return allResources, nil
}

func (s *AzureDiscoveryService) discoverVirtualMachines(ctx context.Context) ([]AzureResource, error) {
	fmt.Println("  → Discovering Virtual Machines...")
	time.Sleep(100 * time.Millisecond) // Simulate API call

	// In production: would use armcompute.VirtualMachinesClient
	return []AzureResource{
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-web-01", s.subscriptionID),
			Name:          "vm-web-01",
			Type:          "Microsoft.Compute/virtualMachines",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"vmSize": "Standard_D2s_v3",
				"osType": "Linux",
			},
		},
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-api-01", s.subscriptionID),
			Name:          "vm-api-01",
			Type:          "Microsoft.Compute/virtualMachines",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"vmSize": "Standard_D4s_v3",
				"osType": "Linux",
			},
		},
	}, nil
}

func (s *AzureDiscoveryService) discoverAppServices(ctx context.Context) ([]AzureResource, error) {
	fmt.Println("  → Discovering App Services...")
	time.Sleep(100 * time.Millisecond)

	return []AzureResource{
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.Web/sites/app-frontend", s.subscriptionID),
			Name:          "app-frontend",
			Type:          "Microsoft.Web/sites",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"kind": "app",
				"sku":  "Standard S1",
			},
		},
	}, nil
}

func (s *AzureDiscoveryService) discoverAKSClusters(ctx context.Context) ([]AzureResource, error) {
	fmt.Println("  → Discovering AKS Clusters...")
	time.Sleep(100 * time.Millisecond)

	return []AzureResource{
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.ContainerService/managedClusters/aks-prod", s.subscriptionID),
			Name:          "aks-prod",
			Type:          "Microsoft.ContainerService/managedClusters",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"kubernetesVersion": "1.28.0",
				"nodeCount":         3,
			},
		},
	}, nil
}

func (s *AzureDiscoveryService) discoverSQLDatabases(ctx context.Context) ([]AzureResource, error) {
	fmt.Println("  → Discovering SQL Databases...")
	time.Sleep(100 * time.Millisecond)

	return []AzureResource{
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.Sql/servers/sql-prod/databases/db-main", s.subscriptionID),
			Name:          "db-main",
			Type:          "Microsoft.Sql/databases",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"edition": "Standard",
				"tier":    "S2",
			},
		},
	}, nil
}

func (s *AzureDiscoveryService) discoverStorageAccounts(ctx context.Context) ([]AzureResource, error) {
	fmt.Println("  → Discovering Storage Accounts...")
	time.Sleep(100 * time.Millisecond)

	return []AzureResource{
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.Storage/storageAccounts/storprod001", s.subscriptionID),
			Name:          "storprod001",
			Type:          "Microsoft.Storage/storageAccounts",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"sku":  "Standard_LRS",
				"kind": "StorageV2",
			},
		},
	}, nil
}

func (s *AzureDiscoveryService) discoverLoadBalancers(ctx context.Context) ([]AzureResource, error) {
	fmt.Println("  → Discovering Load Balancers...")
	time.Sleep(100 * time.Millisecond)

	return []AzureResource{
		{
			ID:            fmt.Sprintf("/subscriptions/%s/resourceGroups/rg-prod/providers/Microsoft.Network/loadBalancers/lb-prod", s.subscriptionID),
			Name:          "lb-prod",
			Type:          "Microsoft.Network/loadBalancers",
			Location:      "eastus",
			ResourceGroup: "rg-prod",
			Properties: map[string]interface{}{
				"sku": "Standard",
			},
		},
	}, nil
}

// BuildDependencyGraph builds a simple dependency graph from resources
func (s *AzureDiscoveryService) BuildDependencyGraph(resources []AzureResource) map[string][]string {
	fmt.Println("\n📊 Building dependency graph...")

	graph := make(map[string][]string)

	// Find resources by type
	var loadBalancers, databases, storageAccounts []AzureResource
	for _, r := range resources {
		switch r.Type {
		case "Microsoft.Network/loadBalancers":
			loadBalancers = append(loadBalancers, r)
		case "Microsoft.Sql/databases":
			databases = append(databases, r)
		case "Microsoft.Storage/storageAccounts":
			storageAccounts = append(storageAccounts, r)
		}
	}

	for _, resource := range resources {
		var dependencies []string

		// VMs and AKS clusters might depend on load balancers
		if resource.Type == "Microsoft.Compute/virtualMachines" || resource.Type == "Microsoft.ContainerService/managedClusters" {
			for _, lb := range loadBalancers {
				dependencies = append(dependencies, lb.ID)
			}
		}

		// App Services and AKS might depend on databases and storage
		if resource.Type == "Microsoft.Web/sites" || resource.Type == "Microsoft.ContainerService/managedClusters" {
			for _, db := range databases {
				dependencies = append(dependencies, db.ID)
			}
			for _, storage := range storageAccounts {
				dependencies = append(dependencies, storage.ID)
			}
		}

		graph[resource.ID] = dependencies
	}

	return graph
}

func getResourceName(resourceID string) string {
	parts := strings.Split(resourceID, "/")
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return resourceID
}

func main() {
	fmt.Println(strings.Repeat("=", 80))
	fmt.Println("Azure Resource Discovery POC - Go")
	fmt.Println(strings.Repeat("=", 80))
	fmt.Println()

	// Simulated subscription ID
	subscriptionID := "12345678-1234-1234-1234-123456789abc"

	// Create discovery service
	discovery := NewAzureDiscoveryService(subscriptionID)

	// Measure performance
	startTime := time.Now()

	// Discover resources
	ctx := context.Background()
	resources, err := discovery.DiscoverAllResources(ctx)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	// Build dependency graph
	dependencyGraph := discovery.BuildDependencyGraph(resources)

	elapsed := time.Since(startTime)

	// Display results
	fmt.Printf("\n✅ Discovery complete!\n")
	fmt.Printf("   Time elapsed: %.2fs\n", elapsed.Seconds())
	fmt.Printf("   Resources found: %d\n", len(resources))
	fmt.Println()

	fmt.Println("📋 Discovered Resources:")
	for _, resource := range resources {
		fmt.Printf("   • %s (%s)\n", resource.Name, resource.Type)
	}

	fmt.Println()
	fmt.Println("🔗 Dependency Graph:")
	for resourceID, dependencies := range dependencyGraph {
		resourceName := getResourceName(resourceID)
		if len(dependencies) > 0 {
			fmt.Printf("   • %s depends on:\n", resourceName)
			for _, dep := range dependencies {
				depName := getResourceName(dep)
				fmt.Printf("     - %s\n", depName)
			}
		}
	}

	fmt.Println()
	fmt.Println(strings.Repeat("=", 80))
	fmt.Println("Go POC Summary:")
	fmt.Println(strings.Repeat("=", 80))
	fmt.Println("✅ Pros:")
	fmt.Println("   • Excellent concurrency with goroutines and channels")
	fmt.Println("   • Superior performance (compiled, no GIL)")
	fmt.Println("   • Strong static typing at compile time")
	fmt.Println("   • Fast startup and low memory footprint")
	fmt.Println("   • Good Azure SDK support")
	fmt.Println()
	fmt.Println("⚠️  Cons:")
	fmt.Println("   • More verbose error handling")
	fmt.Println("   • Steeper learning curve for some developers")
	fmt.Println("   • Less rich ecosystem compared to Python")
	fmt.Println("   • More boilerplate code")
	fmt.Println()
}
