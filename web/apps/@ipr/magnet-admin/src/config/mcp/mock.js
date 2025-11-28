export const mock = [
  {
    name: 'HubSpot',
    system_name: 'BRIDGE_HUBSPOT',
    transport: 'streamable-http',
    url: 'http://127.0.0.1:8011/servers/hubspot/mcp/',
    headers: {
      Authorization: 'Bearer {API_KEY}',
    },
    secrets_names: ['API_KEY'],
    tools: [
      {
        name: 'hubspot-get-user-details',
        description:
          "\n    🎯 Purpose\n      1. Authenticates and analyzes the current HubSpot access token, providing context about the user's permissions and account details.\n\n    🧭 Usage Guidance:\n      1. This tool must be used before performing any operations with Hubspot tools to determine the identity of the user, and permissions they have on their Hubspot account.\n\n    📦 Returns:\n      1. User ID, Hub ID, App ID, token type, a comprehensive list of authorized API scopes, and detailed owner information, and account information.\n      2. The uiDomain and hubId can be used to construct URLs to the HubSpot UI for the user.\n      3. If the user is an owner, the ownerId will help identify objects that are owned by the user.\n  ",
        inputSchema: {
          type: 'object',
          properties: {},
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get User Details',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-list-objects',
        description:
          '\n    🎯 Purpose:\n      1. Retrieves a paginated list of objects of a specified type from HubSpot.\n\n    📦 Returns:\n      1. Collection of objects with their properties and metadata, plus pagination information.\n\n    🧭 Usage Guidance:\n      1. Use for initial data exploration to understand the data structure of a HubSpot object type.\n      2. Helps list objects when the search criteria or filter criteria is not clear.\n      3. Use hubspot-search-objects for targeted queries when the data structure is known.\n      4. Use hubspot-batch-read-objects to retrieve specific objects by their IDs.\n      5. Use hubspot-list-associations to list associations between objects.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to list. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            limit: {
              type: 'integer',
              minimum: 1,
              maximum: 500,
              default: 100,
              description: 'The maximum number of results to display per page (max: 500).',
            },
            after: {
              type: 'string',
              description: 'The paging cursor token of the last successfully read resource.',
            },
            properties: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'A list of the properties to be returned in the response.',
            },
            associations: {
              type: 'array',
              items: {
                type: 'string',
              },
              description:
                'A list of object types to retrieve associated IDs for (e.g., appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users).',
            },
            archived: {
              type: 'boolean',
              default: false,
              description: 'Whether to return only results that have been archived.',
            },
          },
          required: ['objectType'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'List CRM Objects',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-search-objects',
        description:
          '\n    🎯 Purpose:\n      1. Performs advanced filtered searches across HubSpot object types using complex criteria.\n\n    📋 Prerequisites:\n      1. Use the hubspot-list-objects tool to sample existing objects for the object type.\n      2. If hubspot-list-objects tool\'s response isn\'t helpful, use hubspot-list-properties tool.\n\n    📦 Returns:\n      1. Filtered collection matching specific criteria with pagination information.\n\n    🧭 Usage Guidance:\n      1. Preferred for targeted data retrieval when exact filtering criteria are known. Supports complex boolean logic through filter groups.\n      2. Use hubspot-list-objects when filter criteria is not specified or clear or when a search fails.\n      3. Use hubspot-batch-read-objects to retrieve specific objects by their IDs.\n      4. Use hubspot-list-associations to get the associations between objects.\n\n    🔍 Filtering Capabilities:\n      1. Think of "filterGroups" as separate search conditions that you want to combine with OR logic (meaning ANY of them can match).\n      2. If you want to find things that match ALL of several conditions (AND logic), put those conditions together in the same filters list.\n      3. If you want to find things that match AT LEAST ONE of several conditions (OR logic), put each condition in a separate filterGroup.\n      4. You can include a maximum of five filterGroups with up to 6 filters in each group, with a maximum of 18 filters in total.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to search. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            query: {
              type: 'string',
              description:
                'Text to search across default searchable properties of the specified object type. Each object type has different searchable properties. For example: contacts (firstname, lastname, email, phone, company), companies (name, website, domain, phone), deals (dealname, pipeline, dealstage, description, dealtype), etc',
            },
            limit: {
              type: 'integer',
              minimum: 1,
              maximum: 100,
              default: 10,
              description: 'The maximum number of results to display per page (max: 100).',
            },
            after: {
              type: 'string',
              description: 'The paging cursor token of the last successfully read resource.',
            },
            properties: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'A list of the properties to be returned in the response.',
            },
            sorts: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  propertyName: {
                    type: 'string',
                    description: 'The name of the property to sort by',
                  },
                  direction: {
                    type: 'string',
                    enum: ['ASCENDING', 'DESCENDING'],
                    description: 'The sort direction',
                  },
                },
                required: ['propertyName', 'direction'],
                additionalProperties: false,
              },
              description: 'A list of sort criteria to apply to the results.',
            },
            filterGroups: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  filters: {
                    type: 'array',
                    items: {
                      type: 'object',
                      properties: {
                        propertyName: {
                          type: 'string',
                          description: 'The name of the property to filter by',
                        },
                        operator: {
                          type: 'string',
                          enum: [
                            'EQ',
                            'NEQ',
                            'LT',
                            'LTE',
                            'GT',
                            'GTE',
                            'BETWEEN',
                            'IN',
                            'NOT_IN',
                            'HAS_PROPERTY',
                            'NOT_HAS_PROPERTY',
                            'CONTAINS_TOKEN',
                            'NOT_CONTAINS_TOKEN',
                          ],
                          description: 'The operator to use for comparison',
                        },
                        value: {
                          description: 'The value to compare against. Must be a string',
                        },
                        values: {
                          type: 'array',
                          description: 'Set of string values for multi-value operators like IN and NOT_IN.',
                        },
                        highValue: {
                          description: 'The upper bound value for range operators like BETWEEN. The lower bound is specified by the value attribute',
                        },
                      },
                      required: ['propertyName', 'operator'],
                      additionalProperties: false,
                    },
                    description: 'Array of filters to apply (combined with AND).',
                  },
                },
                required: ['filters'],
                additionalProperties: false,
              },
              description: 'Groups of filters to apply (combined with OR).',
            },
          },
          required: ['objectType'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Search CRM Objects',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-create-association',
        description:
          "\n    🛡️ Guardrails:\n      1.  Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Establishes relationships between HubSpot objects, linking records across different object types, by creating an association between two objects.\n\n    📋 Prerequisites:\n      1. Use the hubspot-get-user-details tool to get the OwnerId and UserId if you don't have that already.\n      2. Use the hubspot-get-association-definitions tool to identify valid association types before creating associations.\n  ",
        inputSchema: {
          type: 'object',
          properties: {
            fromObjectType: {
              type: 'string',
              description:
                'The type of HubSpot object to create association from. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            fromObjectId: {
              type: 'string',
              description: 'The ID of the object to create association from',
            },
            toObjectType: {
              type: 'string',
              description:
                'The type of HubSpot object to create association to. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            toObjectId: {
              type: 'string',
              description: 'The ID of the object to create association to',
            },
            associations: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  associationCategory: {
                    type: 'string',
                    enum: ['HUBSPOT_DEFINED', 'USER_DEFINED', 'INTEGRATOR_DEFINED'],
                  },
                  associationTypeId: {
                    type: 'integer',
                    exclusiveMinimum: 0,
                  },
                },
                required: ['associationCategory', 'associationTypeId'],
                additionalProperties: false,
              },
              minItems: 1,
              description: 'List of association specifications defining the relationship',
            },
          },
          required: ['fromObjectType', 'fromObjectId', 'toObjectType', 'toObjectId', 'associations'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Create CRM Object Association',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-get-association-definitions',
        description:
          '\n    🎯 Purpose:\n      1. Retrieves valid association types between specific HubSpot object types.\n\n    📦 Returns:\n      1. Array of valid association definitions with type IDs, labels, and categories.\n\n    🧭 Usage Guidance:\n      1. Always use before creating associations to ensure valid relationship types or to help troubleshoot association creation errors.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            fromObjectType: {
              type: 'string',
              description:
                'The type of HubSpot object to get association from. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            toObjectType: {
              type: 'string',
              description:
                'The type of HubSpot object to get association to. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
          },
          required: ['fromObjectType', 'toObjectType'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get CRM Association Types',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-list-associations',
        description:
          "\n    🎯 Purpose:\n      1. Retrieves existing relationships between a specific object and other objects of a particular type.\n      2. For example, you can find all companies that a contact is associated with, all deals related to a company, or discover which customers have an open ticket.\n\n    📦 Returns:\n      1. Collection of associated object IDs and relationship metadata.\n      2. Use hubspot-batch-read-objects to get more information about the associated objects.\n\n    🧭 Usage Guidance:\n      1. Use this tool when mapping relationships between different HubSpot objects to understand your data's connections.\n      2. This tool is ideal when you already know a specific record's ID and need to discover its relationships with other object types.\n      3. Prefer this over hubspot-search-objects tool when exploring established connections rather than filtering by properties or criteria.\n  ",
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to get associations from. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            objectId: {
              type: 'string',
              description: 'The ID of the HubSpot object to get associations from',
            },
            toObjectType: {
              type: 'string',
              description:
                'The type of HubSpot object to get associations to. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            after: {
              type: 'string',
              description: 'Paging cursor token for retrieving the next page of results',
            },
          },
          required: ['objectType', 'objectId', 'toObjectType'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'List CRM Object Associations',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-batch-create-objects',
        description:
          "\n    🛡️ Guardrails:\n      1. Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Creates multiple HubSpot objects of the same objectType in a single API call, optimizing for bulk operations.\n\n    📋 Prerequisites:\n      1. Use the hubspot-get-user-details tool to get the OwnerId and UserId if you don't have that already.\n      2. Use the hubspot-list-objects tool to sample existing objects for the object type.\n      3. Use the hubspot-get-association-definitions tool to identify valid association types before creating associations.\n  ",
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to create. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            inputs: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  properties: {
                    type: 'object',
                    additionalProperties: {
                      type: 'string',
                    },
                    description: 'Object properties as key-value pairs',
                  },
                  associations: {
                    type: 'array',
                    items: {
                      type: 'object',
                      properties: {
                        types: {
                          type: 'array',
                          items: {
                            type: 'object',
                            properties: {
                              associationCategory: {
                                type: 'string',
                                enum: ['HUBSPOT_DEFINED', 'USER_DEFINED', 'INTEGRATOR_DEFINED'],
                              },
                              associationTypeId: {
                                type: 'integer',
                                exclusiveMinimum: 0,
                              },
                            },
                            required: ['associationCategory', 'associationTypeId'],
                            additionalProperties: false,
                          },
                          minItems: 1,
                        },
                        to: {
                          type: 'object',
                          properties: {
                            id: {
                              type: 'string',
                              description: 'ID of the object to associate with',
                            },
                          },
                          required: ['id'],
                          additionalProperties: false,
                        },
                      },
                      required: ['types', 'to'],
                      additionalProperties: false,
                    },
                    description: 'Optional list of associations to create with this object',
                  },
                  objectWriteTraceId: {
                    type: 'string',
                    description: 'Optional trace ID for debugging purposes',
                  },
                },
                required: ['properties'],
                additionalProperties: false,
              },
              minItems: 1,
              maxItems: 100,
              description: 'Array of objects to create (maximum 100 per batch)',
            },
          },
          required: ['objectType', 'inputs'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Create CRM Objects',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-batch-update-objects',
        description:
          "\n    🛡️ Guardrails:\n      1. Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Updates multiple existing HubSpot objects of the same objectType in a single API call.\n      2. Use this tool when the user wants to update one or more existing CRM objects.\n      3. If you are unsure about the property type to update, identify existing properties of the object and ask the user.\n\n    📋 Prerequisites:\n      1. Use the hubspot-get-user-details tool to get the OwnerId and UserId if you don't have that already.\n      2. Use the hubspot-list-objects tool to sample existing objects for the object type.\n      3. If hubspot-list-objects tool's response isn't helpful, use hubspot-list-properties tool.\n  ",
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to update. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            inputs: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  id: {
                    type: 'string',
                    description: 'ID of the object to update',
                  },
                  properties: {
                    type: 'object',
                    additionalProperties: {
                      type: 'string',
                    },
                    description: 'Object properties as key-value pairs',
                  },
                  idProperty: {
                    type: 'string',
                    description: 'Optional unique property name to use as the ID',
                  },
                  objectWriteTraceId: {
                    type: 'string',
                    description: 'Optional trace ID for debugging purposes',
                  },
                },
                required: ['id', 'properties'],
                additionalProperties: false,
              },
              minItems: 1,
              maxItems: 100,
              description: 'Array of objects to update (maximum 100 per batch)',
            },
          },
          required: ['objectType', 'inputs'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Update Multiple CRM Objects',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-batch-read-objects',
        description:
          '\n    🎯 Purpose:\n      1. Retrieves multiple HubSpot objects of the same object type by their IDs in a single batch operation.\n\n    🧭 Usage Guidance:\n      1. Use this tool to retrieve objects when the object IDs are known.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to read. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            inputs: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  id: {
                    type: 'string',
                    description: 'ID of the object to read',
                  },
                },
                required: ['id'],
                additionalProperties: false,
              },
              minItems: 1,
              maxItems: 100,
              description: 'Array of object IDs to read (maximum 100 per batch)',
            },
            properties: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'Optional list of property names to include in the results',
            },
            propertiesWithHistory: {
              type: 'array',
              items: {
                type: 'string',
              },
              description: 'Optional list of property names to include with history',
            },
          },
          required: ['objectType', 'inputs'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Read Multiple CRM Objects',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-list-properties',
        description:
          '\n    🎯 Purpose:\n      1. This tool retrieves a complete catalog of properties for any HubSpot object type.\n\n    🧭 Usage Guidance:\n      1. This API has a large response that can consume a lot of tokens. Use the hubspot-list-objects tool to sample existing objects for the object type first.\n      2. Try to use the hubspot-get-property tool to get a specific property.\n      3. Use at the beginning of workflows to understand available data structures.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to get properties for. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            archived: {
              type: 'boolean',
              default: false,
              description: 'Whether to return only properties that have been archived.',
            },
            includeHidden: {
              type: 'boolean',
              default: false,
              description: 'Whether to include hidden properties in the response.',
            },
          },
          required: ['objectType'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'List CRM Properties',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-get-property',
        description:
          '\n    🎯 Purpose:\n      1. This tool retrieves detailed information about a specific property for a HubSpot object type.\n      2. You can use this to get all metadata related to a property, including its type, options,\n         and other configuration details.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object the property belongs to. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            propertyName: {
              type: 'string',
              description: 'The name of the property to retrieve',
            },
          },
          required: ['objectType', 'propertyName'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get CRM Property Details',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-create-property',
        description:
          "\n    🛡️ Guardrails:\n      1. Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Creates new custom properties for HubSpot object types, enabling data structure customization.\n\n    📋 Prerequisites:\n      1. Use the hubspot-get-user-details tool to get the OwnerId and UserId if you don't have that already.\n      2. Use the hubspot-list-objects tool to sample existing objects for the object type.\n      3. If hubspot-list-objects tool's response isn't helpful, use hubspot-list-properties tool.\n\n    🧭 Usage Guidance:\n      1. Use this tool when you need to create a new custom property for a HubSpot object type.\n      2. Makes sure that the user is looking to create a new property, and not create an object of a specific object type.\n      3. Use list-properties to get a list of all properties for a given object type to be sure that the property does not already exist.\n      4. Use list-properties to to understand the data structure of object properties first.\n  ",
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object to create the property for. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            name: {
              type: 'string',
              description: 'The internal property name, which must be used when referencing the property via the API',
            },
            label: {
              type: 'string',
              description: 'A human-readable property label that will be shown in HubSpot',
            },
            description: {
              type: 'string',
              description: 'A description of the property that will be shown as help text',
            },
            groupName: {
              type: 'string',
              description: 'The name of the property group the property belongs to',
            },
            type: {
              type: 'string',
              enum: ['string', 'number', 'date', 'datetime', 'enumeration', 'bool'],
              default: 'string',
              description: 'The data type of the property',
            },
            fieldType: {
              type: 'string',
              enum: ['text', 'textarea', 'date', 'file', 'number', 'select', 'radio', 'checkbox', 'booleancheckbox', 'calculation'],
              default: 'text',
              description: 'Controls how the property appears in HubSpot',
            },
            options: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  label: {
                    type: 'string',
                    description: 'The human-readable label for the option',
                  },
                  value: {
                    type: 'string',
                    description: 'The internal value for the option, which must be used when setting the property value',
                  },
                  description: {
                    type: 'string',
                    description: 'A description of what the option represents',
                  },
                  displayOrder: {
                    type: 'integer',
                    description: 'The order for displaying the option (lower numbers displayed first)',
                  },
                  hidden: {
                    type: 'boolean',
                    description: 'Whether the option should be hidden in HubSpot',
                  },
                },
                required: ['label', 'value'],
                additionalProperties: false,
              },
              description: 'A list of valid options for enumeration properties',
            },
            formField: {
              type: 'boolean',
              description: 'Whether the property can be used in forms',
            },
            hidden: {
              type: 'boolean',
              description: 'Whether the property should be hidden in HubSpot',
            },
            displayOrder: {
              type: 'integer',
              description: 'The order for displaying the property (lower numbers displayed first)',
            },
            hasUniqueValue: {
              type: 'boolean',
              description: "Whether the property's value must be unique",
            },
            calculationFormula: {
              type: 'string',
              description: 'A formula that is used to compute a calculated property',
            },
            externalOptions: {
              type: 'boolean',
              description: 'Only for enumeration type properties. Should be set to true in conjunction with a referencedObjectType',
            },
          },
          required: ['objectType', 'name', 'label', 'groupName'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Create CRM Property',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-update-property',
        description:
          "\n    🛡️ Guardrails:\n      1. Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Updates existing custom properties for HubSpot object types, enabling data structure customization.\n\n    🧭 Usage Guidance:\n      1. Use hubspot-list-objects tool to sample existing objects for the object type.\n      2. If hubspot-list-objects tool's response isn't helpful, use hubspot-list-properties tool.\n  ",
        inputSchema: {
          type: 'object',
          properties: {
            objectType: {
              type: 'string',
              description:
                'The type of HubSpot object the property belongs to. Valid values include: appointments, companies, contacts, courses, deals, leads, line_items, listings, marketing_events, meetings, orders, postal_mail, products, quotes, services, subscriptions, tickets, users. For custom objects, use the hubspot-get-schemas tool to get the objectType.',
            },
            propertyName: {
              type: 'string',
              description: 'The name of the property to update',
            },
            label: {
              type: 'string',
              description: 'A human-readable property label that will be shown in HubSpot',
            },
            description: {
              type: 'string',
              description: 'A description of the property that will be shown as help text',
            },
            groupName: {
              type: 'string',
              description: 'The name of the property group the property belongs to',
            },
            type: {
              type: 'string',
              enum: ['string', 'number', 'date', 'datetime', 'enumeration', 'bool'],
              description: 'The data type of the property',
            },
            fieldType: {
              type: 'string',
              enum: ['text', 'textarea', 'date', 'file', 'number', 'select', 'radio', 'checkbox', 'booleancheckbox', 'calculation'],
              description: 'Controls how the property appears in HubSpot',
            },
            options: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  label: {
                    type: 'string',
                    description: 'The human-readable label for the option',
                  },
                  value: {
                    type: 'string',
                    description: 'The internal value for the option, which must be used when setting the property value',
                  },
                  description: {
                    type: 'string',
                    description: 'A description of what the option represents',
                  },
                  displayOrder: {
                    type: 'integer',
                    description: 'The order for displaying the option (lower numbers displayed first)',
                  },
                  hidden: {
                    type: 'boolean',
                    description: 'Whether the option should be hidden in HubSpot',
                  },
                },
                required: ['label', 'value'],
                additionalProperties: false,
              },
              description: 'A list of valid options for enumeration properties',
            },
            formField: {
              type: 'boolean',
              description: 'Whether the property can be used in forms',
            },
            hidden: {
              type: 'boolean',
              description: 'Whether the property should be hidden in HubSpot',
            },
            displayOrder: {
              type: 'integer',
              description: 'The order for displaying the property (lower numbers displayed first)',
            },
            calculationFormula: {
              type: 'string',
              description: 'A formula that is used to compute a calculated property',
            },
          },
          required: ['objectType', 'propertyName'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Update CRM Property',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-create-engagement',
        description:
          '\n    🛡️ Guardrails:\n      1. Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Creates a HubSpot engagement (Note or Task) associated with contacts, companies, deals, or tickets.\n      2. This endpoint is useful for keeping your CRM records up-to-date on any interactions that take place outside of HubSpot.\n      3. Activity reporting in the CRM also feeds off of this data.\n\n    📋 Prerequisites:\n      1. Use the hubspot-get-user-details tool to get the OwnerId and UserId.\n\n    🧭 Usage Guidance:\n      1. Use NOTE type for adding notes to records\n      2. Use TASK type for creating tasks with subject, status, and assignment\n      3. Both require relevant associations to connect them to CRM records\n      4. Other types of engagements (EMAIL, CALL, MEETING) are NOT supported yet.\n      5. HubSpot notes and task descriptions support HTML formatting. However headings (<h1>, <h2>, etc.) look ugly in the CRM. So use them sparingly.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            type: {
              type: 'string',
              enum: ['NOTE', 'TASK'],
              description: 'The type of engagement to create (NOTE or TASK)',
            },
            ownerId: {
              type: 'integer',
              exclusiveMinimum: 0,
              description: 'The ID of the owner of this engagement',
            },
            timestamp: {
              type: 'integer',
              description: 'Timestamp for the engagement (milliseconds since epoch). Defaults to current time if not provided.',
            },
            associations: {
              type: 'object',
              properties: {
                contactIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                companyIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                dealIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                ownerIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                ticketIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
              },
              additionalProperties: false,
              description: 'Associated records for this engagement',
            },
            metadata: {
              type: 'object',
              properties: {},
              additionalProperties: true,
              description: 'Metadata specific to the engagement type',
            },
          },
          required: ['type', 'ownerId', 'associations', 'metadata'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Create Engagement',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: false,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-get-engagement',
        description: '\n    🎯 Purpose:\n      1. Retrieves a HubSpot engagement by ID.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            engagementId: {
              type: 'integer',
              exclusiveMinimum: 0,
              description: 'The ID of the engagement to retrieve',
            },
          },
          required: ['engagementId'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get Engagement',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-update-engagement',
        description:
          '\n    🛡️ Guardrails:\n      1. Data Modification Warning: This tool modifies HubSpot data. Only use when the user has explicitly requested to update their CRM.\n\n    🎯 Purpose:\n      1. Updates an existing HubSpot engagement (Note or Task).\n      2. Allows modification of engagement attributes, content, and metadata.\n\n    📋 Prerequisites:\n      1. You need the engagement ID to update an existing engagement.\n      2. Use the hubspot-get-engagement tool to get the current engagement details if needed.\n      3. Use the hubspot-get-user-details tool to get the owner ID.\n\n    🧭 Usage Guidance:\n      1. Use for updating NOTE content or TASK details (subject, description, status).\n      2. Only include the fields you want to update - other fields will remain unchanged.\n      3. HubSpot notes and task descriptions support HTML formatting. However headings (<h1>, <h2>, etc.) look ugly in the CRM. So use them sparingly.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            engagementId: {
              type: 'integer',
              exclusiveMinimum: 0,
              description: 'The ID of the engagement to update',
            },
            ownerId: {
              type: 'integer',
              exclusiveMinimum: 0,
              description: 'The ID of the owner of this engagement',
            },
            timestamp: {
              type: 'integer',
              description: 'Timestamp for the engagement (milliseconds since epoch).',
            },
            metadata: {
              type: 'object',
              properties: {},
              additionalProperties: true,
              description: 'Metadata specific to the engagement type (Note or Task)',
            },
            associations: {
              type: 'object',
              properties: {
                contactIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                companyIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                dealIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                ownerIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
                ticketIds: {
                  type: 'array',
                  items: {
                    type: 'integer',
                  },
                  default: [],
                },
              },
              additionalProperties: false,
              description: 'Associated records for this engagement',
            },
          },
          required: ['engagementId', 'metadata', 'associations'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Update Engagement',
          readOnlyHint: false,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-generate-feedback-link',
        description:
          "\n    🎯 Purpose:\n      1. Use this tool when the user wants to submit feedback about HubSpot MCP tool.\n      2. Use this tool proactively when the other HubSpot MCP tools are unable to solve the user's tasks effectively.\n      3. Use this tool when you sense dissatisfaction from the user using HubSpot MCP tools.\n      4. Feedback will help us improve the HubSpot MCP tools in future iterations.\n  ",
        inputSchema: {
          type: 'object',
          properties: {},
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Generate Feedback Link',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: false,
        },
      },
      {
        name: 'hubspot-get-schemas',
        description:
          '\n    🎯 Purpose:\n      1. Retrieves all custom object schemas defined in the HubSpot account.\n\n    🧭 Usage Guidance:\n      1. Before working with custom objects to understand available object types,\n         their properties, and associations.\n\n    📦 Returns:\n      1. Provides the objectTypeId and objectType for each schema.\n      2. These attributes should be used for this object type instead of "custom" in subsequent requests.\n  ',
        inputSchema: {
          type: 'object',
          properties: {},
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get Object Schemas',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-get-link',
        description:
          '\n    🎯 Purpose:\n      1. Generates HubSpot UI links for different pages based on object types and IDs.\n      2. Supports both index pages (lists of objects) and record pages (specific object details).\n\n    📋 Prerequisites:\n      1. Use the hubspot-get-user-details tool to get the PortalId and UiDomain.\n\n    🧭 Usage Guidance:\n      1. Use to generate links to HubSpot UI pages when users need to reference specific HubSpot records.\n      2. Validates that object type IDs exist in the HubSpot system.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            portalId: {
              type: 'string',
              description: 'The HubSpot portal/account ID',
            },
            uiDomain: {
              type: 'string',
              description: "The HubSpot UI domain(e.g., 'app.hubspot.com')",
            },
            pageRequests: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  pagetype: {
                    type: 'string',
                    enum: ['record', 'index'],
                    description: "The type of page to link to: 'record' for a specific object's page, 'index' for a list page",
                  },
                  objectTypeId: {
                    type: 'string',
                    description: "The HubSpot object type ID to link to (e.g., '0-1', '0-2' for contacts, companies, or '2-x' for custom objects)",
                  },
                  objectId: {
                    type: 'string',
                    description: "The specific object ID to link to (required for 'record' page types)",
                  },
                },
                required: ['pagetype', 'objectTypeId'],
                additionalProperties: false,
              },
              description: 'Array of page link requests to generate',
            },
          },
          required: ['portalId', 'uiDomain', 'pageRequests'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get HubSpot Link',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: false,
        },
      },
      {
        name: 'hubspot-list-workflows',
        description:
          '\n    🎯 Purpose:\n      1. This tool retrieves a paginated list of workflows from the HubSpot account.\n\n    🧭 Usage Guidance:\n      1. Use the "limit" parameter to control the number of results returned per page.\n      2. For pagination, use the "after" parameter with the value from the previous response\'s paging.next.after.\n      3. This endpoint returns essential workflow information including ID, name, type, and status.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            limit: {
              type: 'number',
              minimum: 1,
              maximum: 100,
              default: 20,
              description: 'The maximum number of workflows to return per page (1-100).',
            },
            after: {
              type: 'string',
              description: 'Cursor token to fetch the next page of results. Use the paging.next.after value from the previous response.',
            },
          },
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'List HubSpot Workflows',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
      {
        name: 'hubspot-get-workflow',
        description:
          '\n    🎯 Purpose:\n      1. This tool retrieves detailed information about a specific workflow from the HubSpot account.\n\n    🧭 Usage Guidance:\n      1. Use the "flowId" parameter to specify which workflow to retrieve.\n      2. This endpoint returns complete workflow information including actions, enrollment criteria, and scheduling.\n      3. Use the hubspot-list-workflows tool first to identify the workflow ID you need.\n  ',
        inputSchema: {
          type: 'object',
          properties: {
            flowId: {
              type: 'string',
              description: 'The ID of the workflow to retrieve',
            },
          },
          required: ['flowId'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: {
          title: 'Get HubSpot Workflow Details',
          readOnlyHint: true,
          destructiveHint: false,
          idempotentHint: true,
          openWorldHint: true,
        },
      },
    ],
    id: '6853c43bfa914297bf3687c0',
  },
  {
    name: 'Atlassian',
    system_name: 'BRIDGE_ATLASSIAN',
    transport: 'streamable-http',
    url: 'http://127.0.0.1:8011/servers/atlassian/mcp/',
    headers: {
      Authorization: 'Bearer {API_KEY}',
    },
    secrets_names: ['API_KEY'],
    tools: [
      {
        name: 'jira_get_user_profile',
        description:
          '\n    Retrieve profile information for a specific Jira user.\n\n    Args:\n        ctx: The FastMCP context.\n        user_identifier: User identifier (email, username, key, or account ID).\n\n    Returns:\n        JSON string representing the Jira user profile object, or an error object if not found.\n\n    Raises:\n        ValueError: If the Jira client is not configured or available.\n    ',
        inputSchema: {
          properties: {
            user_identifier: {
              description:
                "Identifier for the user (e.g., email address 'user@example.com', username 'johndoe', account ID 'accountid:...', or key for Server/DC).",
              title: 'User Identifier',
              type: 'string',
            },
          },
          required: ['user_identifier'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_issue',
        description:
          "Get details of a specific Jira issue including its Epic links and relationship information.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n        fields: Comma-separated list of fields to return (e.g., 'summary,status,customfield_10010'), a single field as a string (e.g., 'duedate'), '*all' for all fields, or omitted for essentials.\n        expand: Optional fields to expand.\n        comment_limit: Maximum number of comments.\n        properties: Issue properties to return.\n        update_history: Whether to update issue view history.\n\n    Returns:\n        JSON string representing the Jira issue object.\n\n    Raises:\n        ValueError: If the Jira client is not configured or available.\n    ",
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            fields: {
              default: 'created,updated,description,assignee,reporter,issuetype,summary,priority,labels,status',
              description:
                "(Optional) Comma-separated list of fields to return (e.g., 'summary,status,customfield_10010'). You may also provide a single field as a string (e.g., 'duedate'). Use '*all' for all fields (including custom fields), or omit for essential fields only.",
              title: 'Fields',
              type: 'string',
            },
            expand: {
              default: '',
              description:
                "(Optional) Fields to expand. Examples: 'renderedFields' (for rendered content), 'transitions' (for available status transitions), 'changelog' (for history)",
              title: 'Expand',
              type: 'string',
            },
            comment_limit: {
              default: 10,
              description: 'Maximum number of comments to include (0 or null for no comments)',
              maximum: 100,
              minimum: 0,
              title: 'Comment Limit',
              type: 'integer',
            },
            properties: {
              type: 'string',
              description: '(Optional) A comma-separated list of issue properties to return',
              default: '',
              title: 'Properties',
            },
            update_history: {
              default: true,
              description: 'Whether to update the issue view history for the requesting user',
              title: 'Update History',
              type: 'boolean',
            },
          },
          required: ['issue_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_search',
        description:
          'Search Jira issues using JQL (Jira Query Language).\n\n    Args:\n        ctx: The FastMCP context.\n        jql: JQL query string.\n        fields: Comma-separated fields to return.\n        limit: Maximum number of results.\n        start_at: Starting index for pagination.\n        projects_filter: Comma-separated list of project keys to filter by.\n        expand: Optional fields to expand.\n\n    Returns:\n        JSON string representing the search results including pagination info.\n    ',
        inputSchema: {
          properties: {
            jql: {
              description:
                'JQL query string (Jira Query Language). Examples:\n- Find Epics: "issuetype = Epic AND project = PROJ"\n- Find issues in Epic: "parent = PROJ-123"\n- Find by status: "status = \'In Progress\' AND project = PROJ"\n- Find by assignee: "assignee = currentUser()"\n- Find recently updated: "updated >= -7d AND project = PROJ"\n- Find by label: "labels = frontend AND project = PROJ"\n- Find by priority: "priority = High AND project = PROJ"',
              title: 'Jql',
              type: 'string',
            },
            fields: {
              default: 'created,updated,description,assignee,reporter,issuetype,summary,priority,labels,status',
              description:
                "(Optional) Comma-separated fields to return in the results. Use '*all' for all fields, or specify individual fields like 'summary,status,assignee,priority'",
              title: 'Fields',
              type: 'string',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
            start_at: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start At',
              type: 'integer',
            },
            projects_filter: {
              default: '',
              description:
                '(Optional) Comma-separated list of project keys to filter results by. Overrides the environment variable JIRA_PROJECTS_FILTER if provided.',
              title: 'Projects Filter',
              type: 'string',
            },
            expand: {
              default: '',
              description: "(Optional) fields to expand. Examples: 'renderedFields', 'transitions', 'changelog'",
              title: 'Expand',
              type: 'string',
            },
          },
          required: ['jql'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_search_fields',
        description:
          'Search Jira fields by keyword with fuzzy match.\n\n    Args:\n        ctx: The FastMCP context.\n        keyword: Keyword for fuzzy search.\n        limit: Maximum number of results.\n        refresh: Whether to force refresh the field list.\n\n    Returns:\n        JSON string representing a list of matching field definitions.\n    ',
        inputSchema: {
          properties: {
            keyword: {
              default: '',
              description: "Keyword for fuzzy search. If left empty, lists the first 'limit' available fields in their default order.",
              title: 'Keyword',
              type: 'string',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results',
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
            refresh: {
              default: false,
              description: 'Whether to force refresh the field list',
              title: 'Refresh',
              type: 'boolean',
            },
          },
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_project_issues',
        description:
          'Get all issues for a specific Jira project.\n\n    Args:\n        ctx: The FastMCP context.\n        project_key: The project key.\n        limit: Maximum number of results.\n        start_at: Starting index for pagination.\n\n    Returns:\n        JSON string representing the search results including pagination info.\n    ',
        inputSchema: {
          properties: {
            project_key: {
              description: 'The project key',
              title: 'Project Key',
              type: 'string',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
            start_at: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start At',
              type: 'integer',
            },
          },
          required: ['project_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_transitions',
        description:
          'Get available status transitions for a Jira issue.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n\n    Returns:\n        JSON string representing a list of available transitions.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
          },
          required: ['issue_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_worklog',
        description:
          'Get worklog entries for a Jira issue.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n\n    Returns:\n        JSON string representing the worklog entries.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
          },
          required: ['issue_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_download_attachments',
        description:
          'Download attachments from a Jira issue.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n        target_dir: Directory to save attachments.\n\n    Returns:\n        JSON string indicating the result of the download operation.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            target_dir: {
              description: 'Directory where attachments should be saved',
              title: 'Target Dir',
              type: 'string',
            },
          },
          required: ['issue_key', 'target_dir'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_agile_boards',
        description:
          "Get jira agile boards by name, project key, or type.\n\n    Args:\n        ctx: The FastMCP context.\n        board_name: Name of the board (fuzzy search).\n        project_key: Project key.\n        board_type: Board type ('scrum' or 'kanban').\n        start_at: Starting index.\n        limit: Maximum results.\n\n    Returns:\n        JSON string representing a list of board objects.\n    ",
        inputSchema: {
          properties: {
            board_name: {
              default: '',
              description: '(Optional) The name of board, support fuzzy search',
              title: 'Board Name',
              type: 'string',
            },
            project_key: {
              default: '',
              description: "(Optional) Jira project key (e.g., 'PROJ-123')",
              title: 'Project Key',
              type: 'string',
            },
            board_type: {
              default: '',
              description: "(Optional) The type of jira board (e.g., 'scrum', 'kanban')",
              title: 'Board Type',
              type: 'string',
            },
            start_at: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start At',
              type: 'integer',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
          },
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_board_issues',
        description:
          'Get all issues linked to a specific board filtered by JQL.\n\n    Args:\n        ctx: The FastMCP context.\n        board_id: The ID of the board.\n        jql: JQL query string to filter issues.\n        fields: Comma-separated fields to return.\n        start_at: Starting index for pagination.\n        limit: Maximum number of results.\n        expand: Optional fields to expand.\n\n    Returns:\n        JSON string representing the search results including pagination info.\n    ',
        inputSchema: {
          properties: {
            board_id: {
              description: "The id of the board (e.g., '1001')",
              title: 'Board Id',
              type: 'string',
            },
            jql: {
              description:
                'JQL query string (Jira Query Language). Examples:\n- Find Epics: "issuetype = Epic AND project = PROJ"\n- Find issues in Epic: "parent = PROJ-123"\n- Find by status: "status = \'In Progress\' AND project = PROJ"\n- Find by assignee: "assignee = currentUser()"\n- Find recently updated: "updated >= -7d AND project = PROJ"\n- Find by label: "labels = frontend AND project = PROJ"\n- Find by priority: "priority = High AND project = PROJ"',
              title: 'Jql',
              type: 'string',
            },
            fields: {
              default: 'created,updated,description,assignee,reporter,issuetype,summary,priority,labels,status',
              description:
                "Comma-separated fields to return in the results. Use '*all' for all fields, or specify individual fields like 'summary,status,assignee,priority'",
              title: 'Fields',
              type: 'string',
            },
            start_at: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start At',
              type: 'integer',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
            expand: {
              default: 'version',
              description: "Optional fields to expand in the response (e.g., 'changelog').",
              title: 'Expand',
              type: 'string',
            },
          },
          required: ['board_id', 'jql'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_sprints_from_board',
        description:
          "Get jira sprints from board by state.\n\n    Args:\n        ctx: The FastMCP context.\n        board_id: The ID of the board.\n        state: Sprint state ('active', 'future', 'closed'). If None, returns all sprints.\n        start_at: Starting index.\n        limit: Maximum results.\n\n    Returns:\n        JSON string representing a list of sprint objects.\n    ",
        inputSchema: {
          properties: {
            board_id: {
              description: "The id of board (e.g., '1000')",
              title: 'Board Id',
              type: 'string',
            },
            state: {
              default: '',
              description: "Sprint state (e.g., 'active', 'future', 'closed')",
              title: 'State',
              type: 'string',
            },
            start_at: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start At',
              type: 'integer',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
          },
          required: ['board_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_sprint_issues',
        description:
          'Get jira issues from sprint.\n\n    Args:\n        ctx: The FastMCP context.\n        sprint_id: The ID of the sprint.\n        fields: Comma-separated fields to return.\n        start_at: Starting index.\n        limit: Maximum results.\n\n    Returns:\n        JSON string representing the search results including pagination info.\n    ',
        inputSchema: {
          properties: {
            sprint_id: {
              description: "The id of sprint (e.g., '10001')",
              title: 'Sprint Id',
              type: 'string',
            },
            fields: {
              default: 'created,updated,description,assignee,reporter,issuetype,summary,priority,labels,status',
              description:
                "Comma-separated fields to return in the results. Use '*all' for all fields, or specify individual fields like 'summary,status,assignee,priority'",
              title: 'Fields',
              type: 'string',
            },
            start_at: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start At',
              type: 'integer',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
          },
          required: ['sprint_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_link_types',
        description:
          'Get all available issue link types.\n\n    Args:\n        ctx: The FastMCP context.\n\n    Returns:\n        JSON string representing a list of issue link type objects.\n    ',
        inputSchema: {
          properties: {},
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_create_issue',
        description:
          "Create a new Jira issue with optional Epic link or parent for subtasks.\n\n    Args:\n        ctx: The FastMCP context.\n        project_key: The JIRA project key.\n        summary: Summary/title of the issue.\n        issue_type: Issue type (e.g., 'Task', 'Bug', 'Story', 'Epic', 'Subtask').\n        assignee: Assignee's user identifier (string): Email, display name, or account ID (e.g., 'user@example.com', 'John Doe', 'accountid:...').\n        description: Issue description.\n        components: Comma-separated list of component names.\n        additional_fields: Dictionary of additional fields.\n\n    Returns:\n        JSON string representing the created issue object.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client is unavailable.\n    ",
        inputSchema: {
          properties: {
            project_key: {
              description:
                "The JIRA project key (e.g. 'PROJ', 'DEV', 'SUPPORT'). This is the prefix of issue keys in your project. Never assume what it might be, always ask the user.",
              title: 'Project Key',
              type: 'string',
            },
            summary: {
              description: 'Summary/title of the issue',
              title: 'Summary',
              type: 'string',
            },
            issue_type: {
              description:
                "Issue type (e.g. 'Task', 'Bug', 'Story', 'Epic', 'Subtask'). The available types depend on your project configuration. For subtasks, use 'Subtask' (not 'Sub-task') and include parent in additional_fields.",
              title: 'Issue Type',
              type: 'string',
            },
            assignee: {
              default: '',
              description:
                "(Optional) Assignee's user identifier (string): Email, display name, or account ID (e.g., 'user@example.com', 'John Doe', 'accountid:...')",
              title: 'Assignee',
              type: 'string',
            },
            description: {
              default: '',
              description: 'Issue description',
              title: 'Description',
              type: 'string',
            },
            components: {
              default: '',
              description: "(Optional) Comma-separated list of component names to assign (e.g., 'Frontend,API')",
              title: 'Components',
              type: 'string',
            },
            additional_fields: {
              additionalProperties: true,
              description:
                "(Optional) Dictionary of additional fields to set. Examples:\n- Set priority: {'priority': {'name': 'High'}}\n- Add labels: {'labels': ['frontend', 'urgent']}\n- Link to parent (for any issue type): {'parent': 'PROJ-123'}\n- Set Fix Version/s: {'fixVersions': [{'id': '10020'}]}\n- Custom fields: {'customfield_10010': 'value'}",
              title: 'Additional Fields',
              type: 'object',
            },
          },
          required: ['project_key', 'summary', 'issue_type'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_batch_create_issues',
        description:
          'Create multiple Jira issues in a batch.\n\n    Args:\n        ctx: The FastMCP context.\n        issues: JSON array string of issue objects.\n        validate_only: If true, only validates without creating.\n\n    Returns:\n        JSON string indicating success and listing created issues (or validation result).\n\n    Raises:\n        ValueError: If in read-only mode, Jira client unavailable, or invalid JSON.\n    ',
        inputSchema: {
          properties: {
            issues: {
              description:
                'JSON array of issue objects. Each object should contain:\n- project_key (required): The project key (e.g., \'PROJ\')\n- summary (required): Issue summary/title\n- issue_type (required): Type of issue (e.g., \'Task\', \'Bug\')\n- description (optional): Issue description\n- assignee (optional): Assignee username or email\n- components (optional): Array of component names\nExample: [\n  {"project_key": "PROJ", "summary": "Issue 1", "issue_type": "Task"},\n  {"project_key": "PROJ", "summary": "Issue 2", "issue_type": "Bug", "components": ["Frontend"]}\n]',
              title: 'Issues',
              type: 'string',
            },
            validate_only: {
              default: false,
              description: 'If true, only validates the issues without creating them',
              title: 'Validate Only',
              type: 'boolean',
            },
          },
          required: ['issues'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_batch_get_changelogs',
        description:
          'Get changelogs for multiple Jira issues (Cloud only).\n\n    Args:\n        ctx: The FastMCP context.\n        issue_ids_or_keys: List of issue IDs or keys.\n        fields: List of fields to filter changelogs by. None for all fields.\n        limit: Maximum changelogs per issue (-1 for all).\n\n    Returns:\n        JSON string representing a list of issues with their changelogs.\n\n    Raises:\n        NotImplementedError: If run on Jira Server/Data Center.\n        ValueError: If Jira client is unavailable.\n    ',
        inputSchema: {
          properties: {
            issue_ids_or_keys: {
              description: "List of Jira issue IDs or keys, e.g. ['PROJ-123', 'PROJ-124']",
              items: {
                type: 'string',
              },
              title: 'Issue Ids Or Keys',
              type: 'array',
            },
            fields: {
              description: "(Optional) Filter the changelogs by fields, e.g. ['status', 'assignee']. Default to [] for all fields.",
              items: {
                type: 'string',
              },
              title: 'Fields',
              type: 'array',
            },
            limit: {
              default: -1,
              description:
                'Maximum number of changelogs to return in result for each issue. Default to -1 for all changelogs. Notice that it only limits the results in the response, the function will still fetch all the data.',
              title: 'Limit',
              type: 'integer',
            },
          },
          required: ['issue_ids_or_keys'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_update_issue',
        description:
          'Update an existing Jira issue including changing status, adding Epic links, updating fields, etc.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n        fields: Dictionary of fields to update.\n        additional_fields: Optional dictionary of additional fields.\n        attachments: Optional JSON array string or comma-separated list of file paths.\n\n    Returns:\n        JSON string representing the updated issue object and attachment results.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable, or invalid input.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            fields: {
              additionalProperties: true,
              description:
                "Dictionary of fields to update. For 'assignee', provide a string identifier (email, name, or accountId). Example: `{'assignee': 'user@example.com', 'summary': 'New Summary'}`",
              title: 'Fields',
              type: 'object',
            },
            additional_fields: {
              additionalProperties: true,
              description: '(Optional) Dictionary of additional fields to update. Use this for custom fields or more complex updates.',
              title: 'Additional Fields',
              type: 'object',
            },
            attachments: {
              default: '',
              description:
                "(Optional) JSON string array or comma-separated list of file paths to attach to the issue. Example: '/path/to/file1.txt,/path/to/file2.txt' or ['/path/to/file1.txt','/path/to/file2.txt']",
              title: 'Attachments',
              type: 'string',
            },
          },
          required: ['issue_key', 'fields'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_delete_issue',
        description:
          'Delete an existing Jira issue.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n\n    Returns:\n        JSON string indicating success.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: 'Jira issue key (e.g. PROJ-123)',
              title: 'Issue Key',
              type: 'string',
            },
          },
          required: ['issue_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_add_comment',
        description:
          'Add a comment to a Jira issue.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n        comment: Comment text in Markdown.\n\n    Returns:\n        JSON string representing the added comment object.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            comment: {
              description: 'Comment text in Markdown format',
              title: 'Comment',
              type: 'string',
            },
          },
          required: ['issue_key', 'comment'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_add_worklog',
        description:
          'Add a worklog entry to a Jira issue.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n        time_spent: Time spent in Jira format.\n        comment: Optional comment in Markdown.\n        started: Optional start time in ISO format.\n        original_estimate: Optional new original estimate.\n        remaining_estimate: Optional new remaining estimate.\n\n\n    Returns:\n        JSON string representing the added worklog object.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            time_spent: {
              description: "Time spent in Jira format. Examples: '1h 30m' (1 hour and 30 minutes), '1d' (1 day), '30m' (30 minutes), '4h' (4 hours)",
              title: 'Time Spent',
              type: 'string',
            },
            comment: {
              default: '',
              description: '(Optional) Comment for the worklog in Markdown format',
              title: 'Comment',
              type: 'string',
            },
            started: {
              default: '',
              description:
                "(Optional) Start time in ISO format. If not provided, the current time will be used. Example: '2023-08-01T12:00:00.000+0000'",
              title: 'Started',
              type: 'string',
            },
            original_estimate: {
              default: '',
              description: '(Optional) New value for the original estimate',
              title: 'Original Estimate',
              type: 'string',
            },
            remaining_estimate: {
              default: '',
              description: '(Optional) New value for the remaining estimate',
              title: 'Remaining Estimate',
              type: 'string',
            },
          },
          required: ['issue_key', 'time_spent'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_link_to_epic',
        description:
          'Link an existing issue to an epic.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: The key of the issue to link.\n        epic_key: The key of the epic to link to.\n\n    Returns:\n        JSON string representing the updated issue object.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "The key of the issue to link (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            epic_key: {
              description: "The key of the epic to link to (e.g., 'PROJ-456')",
              title: 'Epic Key',
              type: 'string',
            },
          },
          required: ['issue_key', 'epic_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_create_issue_link',
        description:
          "Create a link between two Jira issues.\n\n    Args:\n        ctx: The FastMCP context.\n        link_type: The type of link (e.g., 'Blocks').\n        inward_issue_key: The key of the source issue.\n        outward_issue_key: The key of the target issue.\n        comment: Optional comment text.\n        comment_visibility: Optional dictionary for comment visibility.\n\n    Returns:\n        JSON string indicating success or failure.\n\n    Raises:\n        ValueError: If required fields are missing, invalid input, in read-only mode, or Jira client unavailable.\n    ",
        inputSchema: {
          properties: {
            link_type: {
              description: "The type of link to create (e.g., 'Duplicate', 'Blocks', 'Relates to')",
              title: 'Link Type',
              type: 'string',
            },
            inward_issue_key: {
              description: "The key of the inward issue (e.g., 'PROJ-123')",
              title: 'Inward Issue Key',
              type: 'string',
            },
            outward_issue_key: {
              description: "The key of the outward issue (e.g., 'PROJ-456')",
              title: 'Outward Issue Key',
              type: 'string',
            },
            comment: {
              default: '',
              description: '(Optional) Comment to add to the link',
              title: 'Comment',
              type: 'string',
            },
            comment_visibility: {
              additionalProperties: {
                type: 'string',
              },
              description: "(Optional) Visibility settings for the comment (e.g., {'type': 'group', 'value': 'jira-users'})",
              title: 'Comment Visibility',
              type: 'object',
            },
          },
          required: ['link_type', 'inward_issue_key', 'outward_issue_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_remove_issue_link',
        description:
          'Remove a link between two Jira issues.\n\n    Args:\n        ctx: The FastMCP context.\n        link_id: The ID of the link to remove.\n\n    Returns:\n        JSON string indicating success.\n\n    Raises:\n        ValueError: If link_id is missing, in read-only mode, or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            link_id: {
              description: 'The ID of the link to remove',
              title: 'Link Id',
              type: 'string',
            },
          },
          required: ['link_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_transition_issue',
        description:
          'Transition a Jira issue to a new status.\n\n    Args:\n        ctx: The FastMCP context.\n        issue_key: Jira issue key.\n        transition_id: ID of the transition.\n        fields: Optional dictionary of fields to update during transition.\n        comment: Optional comment for the transition.\n\n    Returns:\n        JSON string representing the updated issue object.\n\n    Raises:\n        ValueError: If required fields missing, invalid input, in read-only mode, or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            issue_key: {
              description: "Jira issue key (e.g., 'PROJ-123')",
              title: 'Issue Key',
              type: 'string',
            },
            transition_id: {
              description:
                "ID of the transition to perform. Use the jira_get_transitions tool first to get the available transition IDs for the issue. Example values: '11', '21', '31'",
              title: 'Transition Id',
              type: 'string',
            },
            fields: {
              additionalProperties: true,
              description:
                "(Optional) Dictionary of fields to update during the transition. Some transitions require specific fields to be set (e.g., resolution). Example: {'resolution': {'name': 'Fixed'}}",
              title: 'Fields',
              type: 'object',
            },
            comment: {
              default: '',
              description: '(Optional) Comment to add during the transition. This will be visible in the issue history.',
              title: 'Comment',
              type: 'string',
            },
          },
          required: ['issue_key', 'transition_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_create_sprint',
        description:
          'Create Jira sprint for a board.\n\n    Args:\n        ctx: The FastMCP context.\n        board_id: Board ID.\n        sprint_name: Sprint name.\n        start_date: Start date (ISO format).\n        end_date: End date (ISO format).\n        goal: Optional sprint goal.\n\n    Returns:\n        JSON string representing the created sprint object.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            board_id: {
              description: "The id of board (e.g., '1000')",
              title: 'Board Id',
              type: 'string',
            },
            sprint_name: {
              description: "Name of the sprint (e.g., 'Sprint 1')",
              title: 'Sprint Name',
              type: 'string',
            },
            start_date: {
              description: 'Start time for sprint (ISO 8601 format)',
              title: 'Start Date',
              type: 'string',
            },
            end_date: {
              description: 'End time for sprint (ISO 8601 format)',
              title: 'End Date',
              type: 'string',
            },
            goal: {
              default: '',
              description: '(Optional) Goal of the sprint',
              title: 'Goal',
              type: 'string',
            },
          },
          required: ['board_id', 'sprint_name', 'start_date', 'end_date'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_update_sprint',
        description:
          'Update jira sprint.\n\n    Args:\n        ctx: The FastMCP context.\n        sprint_id: The ID of the sprint.\n        sprint_name: Optional new name.\n        state: Optional new state (future|active|closed).\n        start_date: Optional new start date.\n        end_date: Optional new end date.\n        goal: Optional new goal.\n\n    Returns:\n        JSON string representing the updated sprint object or an error message.\n\n    Raises:\n        ValueError: If in read-only mode or Jira client unavailable.\n    ',
        inputSchema: {
          properties: {
            sprint_id: {
              description: "The id of sprint (e.g., '10001')",
              title: 'Sprint Id',
              type: 'string',
            },
            sprint_name: {
              default: '',
              description: '(Optional) New name for the sprint',
              title: 'Sprint Name',
              type: 'string',
            },
            state: {
              default: '',
              description: '(Optional) New state for the sprint (future|active|closed)',
              title: 'State',
              type: 'string',
            },
            start_date: {
              default: '',
              description: '(Optional) New start date for the sprint',
              title: 'Start Date',
              type: 'string',
            },
            end_date: {
              default: '',
              description: '(Optional) New end date for the sprint',
              title: 'End Date',
              type: 'string',
            },
            goal: {
              default: '',
              description: '(Optional) New goal for the sprint',
              title: 'Goal',
              type: 'string',
            },
          },
          required: ['sprint_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'jira_get_project_versions',
        description: 'Get all fix versions for a specific Jira project.',
        inputSchema: {
          properties: {
            project_key: {
              description: "Jira project key (e.g., 'PROJ')",
              title: 'Project Key',
              type: 'string',
            },
          },
          required: ['project_key'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_search',
        description:
          'Search Confluence content using simple terms or CQL.\n\n    Args:\n        ctx: The FastMCP context.\n        query: Search query - can be simple text or a CQL query string.\n        limit: Maximum number of results (1-50).\n        spaces_filter: Comma-separated list of space keys to filter by.\n\n    Returns:\n        JSON string representing a list of simplified Confluence page objects.\n    ',
        inputSchema: {
          properties: {
            query: {
              description:
                "Search query - can be either a simple text (e.g. 'project documentation') or a CQL query string. Simple queries use 'siteSearch' by default, to mimic the WebUI search, with an automatic fallback to 'text' search if not supported. Examples of CQL:\n- Basic search: 'type=page AND space=DEV'\n- Personal space search: 'space=\"~username\"' (note: personal space keys starting with ~ must be quoted)\n- Search by title: 'title~\"Meeting Notes\"'\n- Use siteSearch: 'siteSearch ~ \"important concept\"'\n- Use text search: 'text ~ \"important concept\"'\n- Recent content: 'created >= \"2023-01-01\"'\n- Content with specific label: 'label=documentation'\n- Recently modified content: 'lastModified > startOfMonth(\"-1M\")'\n- Content modified this year: 'creator = currentUser() AND lastModified > startOfYear()'\n- Content you contributed to recently: 'contributor = currentUser() AND lastModified > startOfWeek()'\n- Content watched by user: 'watcher = \"user@domain.com\" AND type = page'\n- Exact phrase in content: 'text ~ \"\\\"Urgent Review Required\\\"\" AND label = \"pending-approval\"'\n- Title wildcards: 'title ~ \"Minutes*\" AND (space = \"HR\" OR space = \"Marketing\")'\nNote: Special identifiers need proper quoting in CQL: personal space keys (e.g., \"~username\"), reserved words, numeric IDs, and identifiers with special characters.",
              title: 'Query',
              type: 'string',
            },
            limit: {
              default: 10,
              description: 'Maximum number of results (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
            spaces_filter: {
              default: '',
              description:
                '(Optional) Comma-separated list of space keys to filter results by. Overrides the environment variable CONFLUENCE_SPACES_FILTER if provided.',
              title: 'Spaces Filter',
              type: 'string',
            },
          },
          required: ['query'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_get_page',
        description:
          "Get content of a specific Confluence page by its ID, or by its title and space key.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: Confluence page ID. If provided, 'title' and 'space_key' are ignored.\n        title: The exact title of the page. Must be used with 'space_key'.\n        space_key: The key of the space. Must be used with 'title'.\n        include_metadata: Whether to include page metadata.\n        convert_to_markdown: Convert content to markdown (true) or keep raw HTML (false).\n\n    Returns:\n        JSON string representing the page content and/or metadata, or an error if not found or parameters are invalid.\n    ",
        inputSchema: {
          properties: {
            page_id: {
              default: '',
              description:
                "Confluence page ID (numeric ID, can be found in the page URL). For example, in the URL 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title', the page ID is '123456789'. Provide this OR both 'title' and 'space_key'. If page_id is provided, title and space_key will be ignored.",
              title: 'Page Id',
              type: 'string',
            },
            title: {
              default: '',
              description: "The exact title of the Confluence page. Use this with 'space_key' if 'page_id' is not known.",
              title: 'Title',
              type: 'string',
            },
            space_key: {
              default: '',
              description: "The key of the Confluence space where the page resides (e.g., 'DEV', 'TEAM'). Required if using 'title'.",
              title: 'Space Key',
              type: 'string',
            },
            include_metadata: {
              default: true,
              description: 'Whether to include page metadata such as creation date, last update, version, and labels.',
              title: 'Include Metadata',
              type: 'boolean',
            },
            convert_to_markdown: {
              default: true,
              description:
                'Whether to convert page to markdown (true) or keep it in raw HTML format (false). Raw HTML can reveal macros (like dates) not visible in markdown, but CAUTION: using HTML significantly increases token usage in AI responses.',
              title: 'Convert To Markdown',
              type: 'boolean',
            },
          },
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_get_page_children',
        description:
          'Get child pages of a specific Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        parent_id: The ID of the parent page.\n        expand: Fields to expand.\n        limit: Maximum number of child pages.\n        include_content: Whether to include page content.\n        convert_to_markdown: Convert content to markdown if include_content is true.\n        start: Starting index for pagination.\n\n    Returns:\n        JSON string representing a list of child page objects.\n    ',
        inputSchema: {
          properties: {
            parent_id: {
              description: 'The ID of the parent page whose children you want to retrieve',
              title: 'Parent Id',
              type: 'string',
            },
            expand: {
              default: 'version',
              description: "Fields to expand in the response (e.g., 'version', 'body.storage')",
              title: 'Expand',
              type: 'string',
            },
            limit: {
              default: 25,
              description: 'Maximum number of child pages to return (1-50)',
              maximum: 50,
              minimum: 1,
              title: 'Limit',
              type: 'integer',
            },
            include_content: {
              default: false,
              description: 'Whether to include the page content in the response',
              title: 'Include Content',
              type: 'boolean',
            },
            convert_to_markdown: {
              default: true,
              description:
                'Whether to convert page content to markdown (true) or keep it in raw HTML format (false). Only relevant if include_content is true.',
              title: 'Convert To Markdown',
              type: 'boolean',
            },
            start: {
              default: 0,
              description: 'Starting index for pagination (0-based)',
              minimum: 0,
              title: 'Start',
              type: 'integer',
            },
          },
          required: ['parent_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_get_comments',
        description:
          'Get comments for a specific Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: Confluence page ID.\n\n    Returns:\n        JSON string representing a list of comment objects.\n    ',
        inputSchema: {
          properties: {
            page_id: {
              description:
                "Confluence page ID (numeric ID, can be parsed from URL, e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' -> '123456789')",
              title: 'Page Id',
              type: 'string',
            },
          },
          required: ['page_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_get_labels',
        description:
          'Get labels for a specific Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: Confluence page ID.\n\n    Returns:\n        JSON string representing a list of label objects.\n    ',
        inputSchema: {
          properties: {
            page_id: {
              description:
                "Confluence page ID (numeric ID, can be parsed from URL, e.g. from 'https://example.atlassian.net/wiki/spaces/TEAM/pages/123456789/Page+Title' -> '123456789')",
              title: 'Page Id',
              type: 'string',
            },
          },
          required: ['page_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_add_label',
        description:
          'Add label to an existing Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: The ID of the page to update.\n        name: The name of the label.\n\n    Returns:\n        JSON string representing the updated list of label objects for the page.\n\n    Raises:\n        ValueError: If in read-only mode or Confluence client is unavailable.\n    ',
        inputSchema: {
          properties: {
            page_id: {
              description: 'The ID of the page to update',
              title: 'Page Id',
              type: 'string',
            },
            name: {
              description: 'The name of the label',
              title: 'Name',
              type: 'string',
            },
          },
          required: ['page_id', 'name'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_create_page',
        description:
          'Create a new Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        space_key: The key of the space.\n        title: The title of the page.\n        content: The content in Markdown format.\n        parent_id: Optional parent page ID.\n\n    Returns:\n        JSON string representing the created page object.\n\n    Raises:\n        ValueError: If in read-only mode or Confluence client is unavailable.\n    ',
        inputSchema: {
          properties: {
            space_key: {
              description: "The key of the space to create the page in (usually a short uppercase code like 'DEV', 'TEAM', or 'DOC')",
              title: 'Space Key',
              type: 'string',
            },
            title: {
              description: 'The title of the page',
              title: 'Title',
              type: 'string',
            },
            content: {
              description: 'The content of the page in Markdown format. Supports headings, lists, tables, code blocks, and other Markdown syntax',
              title: 'Content',
              type: 'string',
            },
            parent_id: {
              default: '',
              description: '(Optional) parent page ID. If provided, this page will be created as a child of the specified page',
              title: 'Parent Id',
              type: 'string',
            },
          },
          required: ['space_key', 'title', 'content'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_update_page',
        description:
          'Update an existing Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: The ID of the page to update.\n        title: The new title of the page.\n        content: The new content in Markdown format.\n        is_minor_edit: Whether this is a minor edit.\n        version_comment: Optional comment for this version.\n        parent_id: Optional new parent page ID.\n\n    Returns:\n        JSON string representing the updated page object.\n\n    Raises:\n        ValueError: If Confluence client is not configured or available.\n    ',
        inputSchema: {
          properties: {
            page_id: {
              description: 'The ID of the page to update',
              title: 'Page Id',
              type: 'string',
            },
            title: {
              description: 'The new title of the page',
              title: 'Title',
              type: 'string',
            },
            content: {
              description: 'The new content of the page in Markdown format',
              title: 'Content',
              type: 'string',
            },
            is_minor_edit: {
              default: false,
              description: 'Whether this is a minor edit',
              title: 'Is Minor Edit',
              type: 'boolean',
            },
            version_comment: {
              default: '',
              description: 'Optional comment for this version',
              title: 'Version Comment',
              type: 'string',
            },
            parent_id: {
              default: '',
              description: 'Optional the new parent page ID',
              title: 'Parent Id',
              type: 'string',
            },
          },
          required: ['page_id', 'title', 'content'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_delete_page',
        description:
          'Delete an existing Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: The ID of the page to delete.\n\n    Returns:\n        JSON string indicating success or failure.\n\n    Raises:\n        ValueError: If Confluence client is not configured or available.\n    ',
        inputSchema: {
          properties: {
            page_id: {
              description: 'The ID of the page to delete',
              title: 'Page Id',
              type: 'string',
            },
          },
          required: ['page_id'],
          type: 'object',
        },
        annotations: null,
      },
      {
        name: 'confluence_add_comment',
        description:
          'Add a comment to a Confluence page.\n\n    Args:\n        ctx: The FastMCP context.\n        page_id: The ID of the page to add a comment to.\n        content: The comment content in Markdown format.\n\n    Returns:\n        JSON string representing the created comment.\n\n    Raises:\n        ValueError: If in read-only mode or Confluence client is unavailable.\n    ',
        inputSchema: {
          properties: {
            page_id: {
              description: 'The ID of the page to add a comment to',
              title: 'Page Id',
              type: 'string',
            },
            content: {
              description: 'The comment content in Markdown format',
              title: 'Content',
              type: 'string',
            },
          },
          required: ['page_id', 'content'],
          type: 'object',
        },
        annotations: null,
      },
    ],
    id: '68541d682d2b14684ead7a3b',
  },
  {
    name: 'DeepWili',
    system_name: 'DEEPWIKI',
    transport: 'sse',
    url: 'https://mcp.deepwiki.com/sse',
    headers: null,
    secrets_names: null,
    tools: [
      {
        name: 'read_wiki_structure',
        description: 'Get a list of documentation topics for a GitHub repository',
        inputSchema: {
          type: 'object',
          properties: {
            repoName: {
              type: 'string',
              description: 'GitHub repository: owner/repo (e.g. "facebook/react")',
            },
          },
          required: ['repoName'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: null,
      },
      {
        name: 'read_wiki_contents',
        description: 'View documentation about a GitHub repository',
        inputSchema: {
          type: 'object',
          properties: {
            repoName: {
              type: 'string',
              description: 'GitHub repository: owner/repo (e.g. "facebook/react")',
            },
          },
          required: ['repoName'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: null,
      },
      {
        name: 'ask_question',
        description: 'Ask any question about a GitHub repository',
        inputSchema: {
          type: 'object',
          properties: {
            repoName: {
              type: 'string',
              description: 'GitHub repository: owner/repo (e.g. "facebook/react")',
            },
            question: {
              type: 'string',
              description: 'The question to ask about the repository',
            },
          },
          required: ['repoName', 'question'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: null,
      },
    ],
    id: '685420ad07079a8e9c95b3b9',
  },
  {
    name: 'Fetch',
    system_name: 'FETCH',
    transport: 'streamable-http',
    url: 'https://remote.mcpservers.org/fetch/mcp',
    headers: null,
    secrets_names: null,
    tools: [
      {
        name: 'fetch',
        description: null,
        inputSchema: {
          type: 'object',
          properties: {
            url: {
              type: 'string',
            },
            max_length: {
              type: 'number',
              default: 5000,
            },
            start_index: {
              type: 'number',
              default: 0,
            },
            raw: {
              type: 'boolean',
              default: false,
            },
          },
          required: ['url'],
          additionalProperties: false,
          $schema: 'http://json-schema.org/draft-07/schema#',
        },
        annotations: null,
      },
    ],
    id: '68542121e2d7631596da72ea',
  },
]
