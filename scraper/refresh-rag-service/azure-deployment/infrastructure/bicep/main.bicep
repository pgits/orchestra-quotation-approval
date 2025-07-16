// Main Azure infrastructure for Copilot Knowledge Refresh Service
@description('Prefix for all resource names')
param resourcePrefix string = 'copilot-refresh'

@description('Location for all resources')
param location string = resourceGroup().location

@description('SharePoint tenant name')
param sharePointTenant string = 'hexalinks'

@description('SharePoint site URL')
param sharePointSiteUrl string = 'https://hexalinks.sharepoint.com/sites/QuotationsTeam'

@description('Copilot Studio Agent ID')
param agentId string

@description('Copilot Studio Environment ID')
param environmentId string

@description('Container image tag')
param containerImageTag string = 'latest'

// Variables
var uniqueSuffix = substring(uniqueString(resourceGroup().id), 0, 6)
var containerRegistryName = '${resourcePrefix}acr${uniqueSuffix}'
var managedIdentityName = '${resourcePrefix}-identity'
var containerInstanceName = '${resourcePrefix}-container'
var logAnalyticsWorkspaceName = '${resourcePrefix}-logs'
var applicationInsightsName = '${resourcePrefix}-insights'

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights
resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// Container Registry
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// Managed Identity
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
}

// Role assignment for Power Platform access
resource powerPlatformRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, managedIdentity.id, 'PowerPlatformUser')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '8b896d73-8a98-46a4-9a88-4b4ac8e32c7b') // Power Platform User
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Role assignment for SharePoint access
resource sharePointRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, managedIdentity.id, 'SharePointReader')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'acdd72a7-3385-48ef-bd42-f606fba81ae7') // Reader
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// Container Instance
resource containerInstance 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: containerInstanceName
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    containers: [
      {
        name: 'copilot-uploader'
        properties: {
          image: '${containerRegistry.properties.loginServer}/copilot-uploader:${containerImageTag}'
          ports: [
            {
              port: 8080
              protocol: 'TCP'
            }
          ]
          environmentVariables: [
            {
              name: 'AGENT_ID'
              value: agentId
            }
            {
              name: 'ENVIRONMENT_ID'
              value: environmentId
            }
            {
              name: 'SHAREPOINT_SITE_URL'
              value: sharePointSiteUrl
            }
            {
              name: 'SHAREPOINT_LIBRARY_NAME'
              value: 'Shared Documents'
            }
            {
              name: 'SHAREPOINT_FOLDER_PATH'
              value: 'EC Synnex Files'
            }
            {
              name: 'SHAREPOINT_TENANT'
              value: sharePointTenant
            }
            {
              name: 'FILE_PATTERN'
              value: 'ec-synnex-'
            }
            {
              name: 'SUPPORTED_EXTENSIONS'
              value: '.xls,.xlsx'
            }
            {
              name: 'MAX_FILE_SIZE'
              value: '536870912'
            }
            {
              name: 'CHECK_INTERVAL'
              value: '300'
            }
            {
              name: 'RETRY_ATTEMPTS'
              value: '3'
            }
            {
              name: 'RETRY_DELAY'
              value: '60'
            }
            {
              name: 'AZURE_SUBSCRIPTION_ID'
              value: subscription().subscriptionId
            }
            {
              name: 'AZURE_RESOURCE_GROUP'
              value: resourceGroup().name
            }
            {
              name: 'APPINSIGHTS_INSTRUMENTATION_KEY'
              value: applicationInsights.properties.InstrumentationKey
            }
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
            {
              name: 'ENABLE_AUDIT_TRAIL'
              value: 'true'
            }
          ]
          resources: {
            requests: {
              cpu: 1
              memoryInGB: 2
            }
          }
          volumeMounts: [
            {
              name: 'logs'
              mountPath: '/app/logs'
            }
          ]
        }
      }
    ]
    osType: 'Linux'
    restartPolicy: 'OnFailure'
    imageRegistryCredentials: [
      {
        server: containerRegistry.properties.loginServer
        username: containerRegistry.name
        password: containerRegistry.listCredentials().passwords[0].value
      }
    ]
    volumes: [
      {
        name: 'logs'
        emptyDir: {}
      }
    ]
    diagnostics: {
      logAnalytics: {
        workspaceId: logAnalyticsWorkspace.properties.customerId
        workspaceKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
  dependsOn: [
    powerPlatformRoleAssignment
    sharePointRoleAssignment
  ]
}

// Outputs
output containerRegistryName string = containerRegistry.name
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output managedIdentityId string = managedIdentity.id
output managedIdentityClientId string = managedIdentity.properties.clientId
output containerInstanceFqdn string = containerInstance.properties.ipAddress.fqdn
output applicationInsightsInstrumentationKey string = applicationInsights.properties.InstrumentationKey
output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.properties.customerId