/**
 * Resource Query Component
 * 
 * Interactive interface to ask questions about resources and get intelligent answers
 */

import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  List,
  ListItem,
  Card,
  CardContent,
  Chip,
  IconButton,
  Alert,
} from '@mui/material';
import {
  Send as SendIcon,
  QuestionAnswer as QuestionIcon,
  AutoAwesome as AIIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useStore } from '../../store/useStore';
import apiClient from '../../services/api';

interface QueryMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  data?: QueryResult;
}

interface QueryResult {
  answer: string;
  resource_info?: {
    id: string;
    name: string;
    type: string;
    risk_score?: number;
  };
  related_resources?: string[];
  suggestions?: string[];
}

const EXAMPLE_QUERIES = [
  'What resources depend on [resource-name]?',
  'Which resources are single points of failure?',
  'What is the risk score for [resource-name]?',
  'Show me all databases in Azure',
  'What would happen if [resource-name] fails?',
];

export default function ResourceQuery() {
  const { topology } = useStore();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<QueryMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSendQuery = async () => {
    if (!query.trim() || loading) return;

    const userMessage: QueryMessage = {
      id: crypto.randomUUID(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      // Parse the query to determine what information to fetch
      const result = await processQuery(query.toLowerCase());

      const assistantMessage: QueryMessage = {
        id: crypto.randomUUID(),
        type: 'assistant',
        content: result.answer,
        timestamp: new Date(),
        data: result,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Query processing failed:', err);
      const errorMessage: QueryMessage = {
        id: crypto.randomUUID(),
        type: 'assistant',
        content: 'I encountered an error processing your query. Please try rephrasing your question.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const processQuery = async (query: string): Promise<QueryResult> => {
    const resources = topology?.nodes || [];

    // Query: List all resources
    if (query.includes('list all') || query.includes('show all') || query.includes('show me all')) {
      const resourceTypes = [...new Set(resources.map((r) => r.resource_type))];
      return {
        answer: `I found ${resources.length} resources across ${resourceTypes.length} types: ${resourceTypes.slice(0, 5).join(', ')}${resourceTypes.length > 5 ? '...' : ''}`,
        suggestions: [
          'What is the risk score for a specific resource?',
          'Which resources are single points of failure?',
        ],
      };
    }

    // Query: Single points of failure
    if (query.includes('single point') || query.includes('spof')) {
      try {
        const spofs = await apiClient.getAllRisks();
        const criticalResources = spofs.filter((r) => r.single_point_of_failure);
        return {
          answer: `I identified ${criticalResources.length} single points of failure in your infrastructure. These resources have no redundancy and could cause significant impact if they fail.`,
          related_resources: criticalResources.map((r) => r.resource_id),
          suggestions: [
            'What would happen if [resource-name] fails?',
            'Show me the blast radius for a resource',
          ],
        };
      } catch {
        return {
          answer: 'I found some potential single points of failure in your infrastructure based on the topology. Consider adding redundancy to critical resources.',
          suggestions: ['What is the risk score for a specific resource?'],
        };
      }
    }

    // Query: Risk score for a resource
    if (query.includes('risk score') || query.includes('how risky')) {
      // Extract resource name from query
      const resourceName = extractResourceName(query, resources);
      if (resourceName) {
        const resource = resources.find((r) => r.name.toLowerCase().includes(resourceName.toLowerCase()));
        if (resource) {
          try {
            const risk = await apiClient.getRiskAssessment(resource.id);
            return {
              answer: `${resource.name} has a risk score of ${risk.risk_score.toFixed(1)}/100. It is considered ${risk.criticality} criticality with ${risk.dependencies_count} dependencies and ${risk.dependents_count} dependents.`,
              resource_info: {
                id: resource.id,
                name: resource.name,
                type: resource.resource_type,
                risk_score: risk.risk_score,
              },
              suggestions: [
                'What would happen if this resource fails?',
                'Show me resources that depend on this',
              ],
            };
          } catch {
            return {
              answer: `Unable to get exact risk score for ${resource.name}, but I can see it has connections to other resources in the topology.`,
            };
          }
        }
      }
      return {
        answer: 'Please specify a resource name to get its risk score. You can ask: "What is the risk score for [resource-name]?"',
        suggestions: EXAMPLE_QUERIES,
      };
    }

    // Query: Dependencies
    if (query.includes('depend') || query.includes('connected to')) {
      const resourceName = extractResourceName(query, resources);
      if (resourceName) {
        const resource = resources.find((r) => r.name.toLowerCase().includes(resourceName.toLowerCase()));
        if (resource) {
          try {
            const deps = await apiClient.getResourceDependencies(resource.id);
            return {
              answer: `${resource.name} has ${deps.upstream.length} upstream dependencies and ${deps.downstream.length} downstream dependents. ${deps.downstream.length > 0 ? `If it fails, ${deps.downstream.length} resources would be directly affected.` : ''}`,
              resource_info: {
                id: resource.id,
                name: resource.name,
                type: resource.resource_type,
              },
              related_resources: [...deps.upstream.map((r) => r.id), ...deps.downstream.map((r) => r.id)],
            };
          } catch {
            return {
              answer: `I can see ${resource.name} in the topology, but I need more information to determine its exact dependencies.`,
            };
          }
        }
      }
      return {
        answer: 'Please specify which resource you want to know about. You can ask: "What resources depend on [resource-name]?"',
        suggestions: EXAMPLE_QUERIES,
      };
    }

    // Query: Failure impact
    if (query.includes('fail') || query.includes('blast radius') || query.includes('what happens')) {
      const resourceName = extractResourceName(query, resources);
      if (resourceName) {
        const resource = resources.find((r) => r.name.toLowerCase().includes(resourceName.toLowerCase()));
        if (resource) {
          try {
            const blastRadius = await apiClient.getBlastRadius(resource.id);
            return {
              answer: `If ${resource.name} fails, it would directly affect ${blastRadius.directly_affected.length} resources and indirectly impact ${blastRadius.indirectly_affected.length} more. Total blast radius: ${blastRadius.total_affected} resources. User impact: ${blastRadius.user_impact}.`,
              resource_info: {
                id: resource.id,
                name: resource.name,
                type: resource.resource_type,
              },
              related_resources: [
                ...blastRadius.directly_affected.map((r: { id: string }) => r.id),
                ...blastRadius.indirectly_affected.slice(0, 5).map((r: { id: string }) => r.id),
              ],
            };
          } catch {
            return {
              answer: `${resource.name} appears to be connected to other resources. A failure could have cascading effects on dependent systems.`,
            };
          }
        }
      }
      return {
        answer: 'Please specify which resource you want to analyze. You can ask: "What would happen if [resource-name] fails?"',
        suggestions: EXAMPLE_QUERIES,
      };
    }

    // Query: Filter by type or cloud
    if (query.includes('database') || query.includes('service') || query.includes('azure') || query.includes('aws') || query.includes('gcp')) {
      let filtered = resources;
      
      if (query.includes('database')) {
        filtered = filtered.filter((r) => r.resource_type.toLowerCase().includes('database') || r.resource_type.toLowerCase().includes('sql'));
      }
      if (query.includes('azure')) {
        filtered = filtered.filter((r) => r.cloud_provider === 'azure');
      }
      if (query.includes('aws')) {
        filtered = filtered.filter((r) => r.cloud_provider === 'aws');
      }
      if (query.includes('gcp')) {
        filtered = filtered.filter((r) => r.cloud_provider === 'gcp');
      }

      return {
        answer: `I found ${filtered.length} matching resources. ${filtered.slice(0, 3).map((r) => r.name).join(', ')}${filtered.length > 3 ? '...' : ''}`,
        related_resources: filtered.slice(0, 10).map((r) => r.id),
        suggestions: ['What is the risk score for these resources?'],
      };
    }

    // Default response
    return {
      answer: "I'm here to help you understand your infrastructure! You can ask me about resource dependencies, risk scores, failure impacts, and more. Try one of the example queries below.",
      suggestions: EXAMPLE_QUERIES,
    };
  };

  const extractResourceName = (query: string, resources: { name: string }[]): string | null => {
    // Try to find a resource name in the query
    for (const resource of resources) {
      if (query.toLowerCase().includes(resource.name.toLowerCase())) {
        return resource.name;
      }
    }
    // Look for text in quotes or brackets
    const quoted = query.match(/["']([^"']+)["']/);
    if (quoted) return quoted[1];
    const bracketed = query.match(/\[([^\]]+)\]/);
    if (bracketed) return bracketed[1];
    return null;
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <AIIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Resource Query Assistant
            </Typography>
          </Box>
          {messages.length > 0 && (
            <IconButton onClick={clearConversation} size="small">
              <ClearIcon />
            </IconButton>
          )}
        </Box>
        <Typography variant="body2" color="text.secondary" paragraph>
          Ask me anything about your resources, dependencies, risks, and infrastructure
        </Typography>

        {/* Example Queries */}
        {messages.length === 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Try asking:
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1}>
              {EXAMPLE_QUERIES.map((example, index) => (
                <Chip
                  key={index}
                  label={example}
                  onClick={() => handleExampleClick(example)}
                  size="small"
                  variant="outlined"
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          </Box>
        )}
      </Paper>

      {/* Conversation Area */}
      {messages.length > 0 && (
        <Paper sx={{ p: 3, mb: 3, maxHeight: 500, overflowY: 'auto' }}>
          <List>
            {messages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  flexDirection: 'column',
                  alignItems: message.type === 'user' ? 'flex-end' : 'flex-start',
                  mb: 2,
                }}
              >
                <Card
                  sx={{
                    maxWidth: '80%',
                    background: message.type === 'user' 
                      ? 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)'
                      : '#132f4c',
                  }}
                >
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      {message.type === 'assistant' && <QuestionIcon fontSize="small" />}
                      <Typography variant="caption" color="text.secondary">
                        {message.type === 'user' ? 'You' : 'Assistant'}
                      </Typography>
                    </Box>
                    <Typography variant="body1">
                      {message.content}
                    </Typography>

                    {message.data?.resource_info && (
                      <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <Chip
                          label={`${message.data.resource_info.name} - ${message.data.resource_info.type}`}
                          size="small"
                          color="primary"
                        />
                        {message.data.resource_info.risk_score && (
                          <Chip
                            label={`Risk: ${message.data.resource_info.risk_score.toFixed(1)}`}
                            size="small"
                            color={message.data.resource_info.risk_score > 70 ? 'error' : 'success'}
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    )}

                    {message.data?.suggestions && message.data.suggestions.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                          Suggestions:
                        </Typography>
                        {message.data.suggestions.map((suggestion, index) => (
                          <Chip
                            key={index}
                            label={suggestion}
                            size="small"
                            onClick={() => handleExampleClick(suggestion)}
                            sx={{ mr: 0.5, mb: 0.5, cursor: 'pointer' }}
                          />
                        ))}
                      </Box>
                    )}
                  </CardContent>
                </Card>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                  {message.timestamp.toLocaleTimeString()}
                </Typography>
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Query Input */}
      <Paper sx={{ p: 2 }}>
        <Box display="flex" gap={2}>
          <TextField
            fullWidth
            placeholder="Ask about resources, dependencies, risks..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendQuery()}
            disabled={loading}
            multiline
            maxRows={3}
          />
          <Button
            variant="contained"
            onClick={handleSendQuery}
            disabled={!query.trim() || loading}
            startIcon={<SendIcon />}
          >
            {loading ? 'Thinking...' : 'Send'}
          </Button>
        </Box>
      </Paper>

      {/* Info Alert */}
      {topology?.nodes.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No resources found in topology. Please load your infrastructure data first.
        </Alert>
      )}
    </Box>
  );
}
