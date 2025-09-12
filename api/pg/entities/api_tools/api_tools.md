
```json
{
  "_id": {
    "$oid": "682ef5e2da7159fd0e5f19bc"
  },
  "system_name": "service_IPRAccountBS_addPromotionComponent__post",
  "name": "service_IPRAccountBS_addPromotionComponent__post",
  "description": "addPromotionComponent",
  "id": null,
  "variants": [
    {
      "variant": "variant_1",
      "description": null,
      "value": {
        "parameters": {
          "input": {
            "type": "object",
            "properties": {
              "requestBody": {
                "required": [
                  "ProductId",
                  "PromotionInstanceId"
                ],
                "type": "object",
                "properties": {
                  "ProductId": {
                    "title": "ProductId",
                    "type": "string",
                    "x-siebel-datatype": "String"
                  },
                  "PromotionInstanceId": {
                    "title": "PromotionInstanceId",
                    "type": "string",
                    "x-siebel-datatype": "String"
                  }
                }
              },
              "queryParams": {
                "type": "object",
                "properties": {
                  "matchrequestformat": {
                    "type": "string",
                    "enum": [
                      "Y"
                    ],
                    "default": "Y",
                    "description": ""
                  },
                  "excludeEmptyFieldsInResponse": {
                    "type": "string",
                    "default": "false",
                    "description": ""
                  }
                },
                "required": [
                  "matchrequestformat"
                ]
              }
            },
            "required": [
              "requestBody",
              "queryParams"
            ]
          },
          "output": {}
        }
      }
    }
  ],
  "active_variant": "variant_1",
  "api_provider": "SIEBEL_OPEN_INTEGRATOR",
  "path": "/service/IPRAccountBS/addPromotionComponent/",
  "method": "POST",
  "mock": null,
  "original_parameters": {
    "input": {
      "type": "object",
      "properties": {
        "requestBody": {
          "required": [
            "ProductId",
            "PromotionInstanceId"
          ],
          "type": "object",
          "properties": {
            "ProductId": {
              "title": "ProductId",
              "type": "string",
              "x-siebel-datatype": "String"
            },
            "PromotionInstanceId": {
              "title": "PromotionInstanceId",
              "type": "string",
              "x-siebel-datatype": "String"
            }
          }
        },
        "queryParams": {
          "type": "object",
          "properties": {
            "matchrequestformat": {
              "type": "string",
              "enum": [
                "Y"
              ],
              "default": "Y",
              "description": ""
            },
            "excludeEmptyFieldsInResponse": {
              "type": "string",
              "default": "false",
              "description": ""
            }
          },
          "required": [
            "matchrequestformat"
          ]
        }
      },
      "required": [
        "requestBody",
        "queryParams"
      ]
    },
    "output": {}
  },
  "original_operation_definition": {
    "tags": [
      "service/IPRAccountBS/addPromotionComponent/"
    ],
    "operationId": "service_IPRAccountBS_addPromotionComponent__post",
    "parameters": [
      {
        "name": "matchrequestformat",
        "in": "query",
        "required": true,
        "schema": {
          "type": "string",
          "enum": [
            "Y"
          ],
          "default": "Y"
        }
      },
      {
        "name": "excludeEmptyFieldsInResponse",
        "in": "query",
        "schema": {
          "type": "string",
          "default": "false"
        }
      }
    ],
    "requestBody": {
      "content": {
        "application/json": {
          "schema": {
            "required": [
              "ProductId",
              "PromotionInstanceId"
            ],
            "type": "object",
            "properties": {
              "ProductId": {
                "title": "ProductId",
                "type": "string",
                "x-siebel-datatype": "String"
              },
              "PromotionInstanceId": {
                "title": "PromotionInstanceId",
                "type": "string",
                "x-siebel-datatype": "String"
              }
            }
          }
        },
        "application/xml": {
          "schema": {
            "required": [
              "ProductId",
              "PromotionInstanceId"
            ],
            "type": "object",
            "properties": {
              "ProductId": {
                "title": "ProductId",
                "type": "string",
                "x-siebel-datatype": "String"
              },
              "PromotionInstanceId": {
                "title": "PromotionInstanceId",
                "type": "string",
                "x-siebel-datatype": "String"
              }
            }
          }
        }
      },
      "required": true
    },
    "responses": {
      "200": {
        "description": "Successful Operation",
        "content": {
          "application/json": {
            "schema": {
              "type": "object",
              "properties": {
                "OrderId": {
                  "title": "OrderId",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "PromotionRuleId": {
                  "title": "PromotionRuleId",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "PromotionId": {
                  "title": "PromotionId",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "PromotionRoots": {
                  "title": "PromotionRoots",
                  "type": "object",
                  "properties": {
                    "MessageId": {
                      "type": "string",
                      "example": ""
                    },
                    "MessageType": {
                      "type": "string",
                      "example": "Integration Object"
                    },
                    "IntObjectName": {
                      "type": "string",
                      "example": "SIS OM Order"
                    },
                    "IntObjectFormat": {
                      "type": "string",
                      "example": "Siebel Hierarchical"
                    },
                    "ListOfSIS OM Order": {
                      "type": "object",
                      "properties": {
                        "Header": {
                          "minItems": 1,
                          "type": "array",
                          "items": {
                            "type": "object",
                            "properties": {
                              "Account": {
                                "title": "Account",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "100",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Account Location": {
                                "title": "Account Location",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "50",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "City": {
                                "title": "City",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Conflict Id": {
                                "title": "Conflict Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Country": {
                                "title": "Country",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Created": {
                                "title": "Created",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_DATETIME"
                              },
                              "Discount": {
                                "title": "Discount",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_NUMBER"
                              },
                              "Id": {
                                "title": "Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Name": {
                                "title": "Name",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "75",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Postal Code": {
                                "title": "Postal Code",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "State": {
                                "title": "State",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Updated": {
                                "title": "Updated",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_DATETIME"
                              },
                              "Account Id": {
                                "title": "Account Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Account Type": {
                                "title": "Account Type",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Active": {
                                "title": "Active",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_BOOL"
                              },
                              "Agreement Id": {
                                "title": "Agreement Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Applicant Group Id": {
                                "title": "Applicant Group Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "As Of Date": {
                                "title": "As Of Date",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_UTCDATETIME"
                              },
                              "Billing Account Id": {
                                "title": "Billing Account Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Billing Profile Id": {
                                "title": "Billing Profile Id",
                                "type": "string",
                                "x-maxLength": "15",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Compound Product Number": {
                                "title": "Compound Product Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "100",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Contact Id": {
                                "title": "Contact Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Currency Code": {
                                "title": "Currency Code",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Discount Amount": {
                                "title": "Discount Amount",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Discount Amount MRC": {
                                "title": "Discount Amount MRC",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Discount Reason": {
                                "title": "Discount Reason",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "250",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Freight": {
                                "title": "Freight",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Integration Id": {
                                "title": "Integration Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Opportunity Id": {
                                "title": "Opportunity Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Order Number": {
                                "title": "Order Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Order Type": {
                                "title": "Order Type",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Pre Pick Mode": {
                                "title": "Pre Pick Mode",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Price List Id": {
                                "title": "Price List Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Quote Id": {
                                "title": "Quote Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Quote Number": {
                                "title": "Quote Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "75",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Requested Ship Date": {
                                "title": "Requested Ship Date",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_DATETIME"
                              },
                              "Revision Number": {
                                "title": "Revision Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_NUMBER"
                              },
                              "Service Account Id": {
                                "title": "Service Account Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Ship To Account Id": {
                                "title": "Ship To Account Id",
                                "type": "string",
                                "x-maxLength": "15",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Ship To Address Id": {
                                "title": "Ship To Address Id",
                                "type": "string",
                                "x-maxLength": "15",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Status": {
                                "title": "Status",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Tax Amount": {
                                "title": "Tax Amount",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Tax Exempt": {
                                "title": "Tax Exempt",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_BOOL"
                              },
                              "Tax Rate": {
                                "title": "Tax Rate",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_NUMBER"
                              },
                              "Price List": {
                                "title": "Price List",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "100",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "ListOfLine Item": {
                                "type": "object",
                                "properties": {
                                  "Line Item": {
                                    "type": "array",
                                    "items": {
                                      "type": "object",
                                      "properties": {
                                        "Action Code": {
                                          "title": "Action Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Adjusted List Price": {
                                          "title": "Adjusted List Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Asset Status": {
                                          "title": "Asset Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Base Price": {
                                          "title": "Base Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Billing Account": {
                                          "title": "Billing Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Billing Type": {
                                          "title": "Billing Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Calc Discount Amount": {
                                          "title": "Calc Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Calc Discount Percent": {
                                          "title": "Calc Discount Percent",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Calculated Asset Status": {
                                          "title": "Calculated Asset Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Calculated Due Date": {
                                          "title": "Calculated Due Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "City": {
                                          "title": "City",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Class Id": {
                                          "title": "Class Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Configuration Model Id": {
                                          "title": "Configuration Model Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Conflict Id": {
                                          "title": "Conflict Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Country": {
                                          "title": "Country",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Created": {
                                          "title": "Created",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Currency Code": {
                                          "title": "Currency Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "15",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Discount": {
                                          "title": "Discount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Discount Amount": {
                                          "title": "Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Discount Amount MRC": {
                                          "title": "Discount Amount MRC",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Discount Percent": {
                                          "title": "Discount Percent",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Discount Percent MRC": {
                                          "title": "Discount Percent MRC",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Discount Source": {
                                          "title": "Discount Source",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Donating Service Provider": {
                                          "title": "Donating Service Provider",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Dynamic Discount Method": {
                                          "title": "Dynamic Discount Method",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Effective End Date": {
                                          "title": "Effective End Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Effective Start Date": {
                                          "title": "Effective Start Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Ending Phone Number": {
                                          "title": "Ending Phone Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "20",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Exclude Pricing Flag": {
                                          "title": "Exclude Pricing Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Forcastable Flag": {
                                          "title": "Forcastable Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Has Generics Flag": {
                                          "title": "Has Generics Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Header Discount Amount": {
                                          "title": "Header Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Header Id": {
                                          "title": "Header Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Id": {
                                          "title": "Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Legacy Account Number": {
                                          "title": "Legacy Account Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "List Price": {
                                          "title": "List Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "MRC CxTotal": {
                                          "title": "MRC CxTotal",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "MRC Search Spec": {
                                          "title": "MRC Search Spec",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Max Price": {
                                          "title": "Max Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Min Price": {
                                          "title": "Min Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "NRC CxTotal": {
                                          "title": "NRC CxTotal",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "NRC Search Spec": {
                                          "title": "NRC Search Spec",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Name": {
                                          "title": "Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Need Refresh": {
                                          "title": "Need Refresh",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Net Price": {
                                          "title": "Net Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Network Element Type": {
                                          "title": "Network Element Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Number Portability Agency Name": {
                                          "title": "Number Portability Agency Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Number To Port": {
                                          "title": "Number To Port",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "20",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Original List Price": {
                                          "title": "Original List Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Original Order Id": {
                                          "title": "Original Order Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Owner Account": {
                                          "title": "Owner Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "PIN": {
                                          "title": "PIN",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Postal Code": {
                                          "title": "Postal Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Price List Id": {
                                          "title": "Price List Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Pricing Adjustment Amount": {
                                          "title": "Pricing Adjustment Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Pricing Comments": {
                                          "title": "Pricing Comments",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "250",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Pricing Commit Type": {
                                          "title": "Pricing Commit Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prod Prom Name": {
                                          "title": "Prod Prom Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prod Prom Type": {
                                          "title": "Prod Prom Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product": {
                                          "title": "Product",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Id": {
                                          "title": "Product Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prom Group Name": {
                                          "title": "Prom Group Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Rule Type": {
                                          "title": "Prom Group Rule Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Quantity": {
                                          "title": "Quantity",
                                          "type": "string",
                                          "x-siebel-precision": "16",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_INTEGER"
                                        },
                                        "Root Id": {
                                          "title": "Root Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Product Id": {
                                          "title": "Root Product Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Promotion Group Id": {
                                          "title": "Root Promotion Group Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Promotion Id": {
                                          "title": "Root Promotion Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Sequence Number": {
                                          "title": "Sequence Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_INTEGER"
                                        },
                                        "Service Account": {
                                          "title": "Service Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Address": {
                                          "title": "Service Address",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Point Id": {
                                          "title": "Service Point Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Service Postal Code": {
                                          "title": "Service Postal Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Price Method": {
                                          "title": "Service Price Method",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Price Percent": {
                                          "title": "Service Price Percent",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Smart Part Number": {
                                          "title": "Smart Part Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "250",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Starting Phone Number": {
                                          "title": "Starting Phone Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "20",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "State": {
                                          "title": "State",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Tax Amount": {
                                          "title": "Tax Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Tier Price Flag": {
                                          "title": "Tier Price Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Service Account": {
                                          "title": "To Service Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Unit Price": {
                                          "title": "Unit Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Updated": {
                                          "title": "Updated",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Volume Discount Item": {
                                          "title": "Volume Discount Item",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Volume Upsell Item": {
                                          "title": "Volume Upsell Item",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Account Id": {
                                          "title": "Account Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Account Type": {
                                          "title": "Account Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Agreement Id": {
                                          "title": "Agreement Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Applicant Group Id": {
                                          "title": "Applicant Group Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Asset Integration Id": {
                                          "title": "Asset Integration Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Asset Member Compatibility": {
                                          "title": "Asset Member Compatibility",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Asset Number": {
                                          "title": "Asset Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Auto Explode Flag": {
                                          "title": "Auto Explode Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Base Line Item Id": {
                                          "title": "Base Line Item Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Billing Account Id": {
                                          "title": "Billing Account Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Billing Profile Id": {
                                          "title": "Billing Profile Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Billing Profile Name": {
                                          "title": "Billing Profile Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "CLLI": {
                                          "title": "CLLI",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cfg Latest Released Flag": {
                                          "title": "Cfg Latest Released Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cfg State Code": {
                                          "title": "Cfg State Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cfg Type": {
                                          "title": "Cfg Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Change Cost": {
                                          "title": "Change Cost",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Commitment Covered Flag": {
                                          "title": "Commitment Covered Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Compound Product Flag": {
                                          "title": "Compound Product Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Compound Product Number": {
                                          "title": "Compound Product Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Contact Id": {
                                          "title": "Contact Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Convert To Agreement Flag": {
                                          "title": "Convert To Agreement Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Convert To Asset Flag": {
                                          "title": "Convert To Asset Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cost": {
                                          "title": "Cost",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Covered Asset Id": {
                                          "title": "Covered Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Current Price": {
                                          "title": "Current Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Deleted Products": {
                                          "title": "Deleted Products",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1000",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Depends on Id": {
                                          "title": "Depends on Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Description": {
                                          "title": "Description",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Due Date": {
                                          "title": "Due Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Effective From": {
                                          "title": "Effective From",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Effective To": {
                                          "title": "Effective To",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Eligibility Reason": {
                                          "title": "Eligibility Reason",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "500",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Eligibility Status": {
                                          "title": "Eligibility Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Exchange Date": {
                                          "title": "Exchange Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Extended Quantity": {
                                          "title": "Extended Quantity",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Extended Quantity Requested": {
                                          "title": "Extended Quantity Requested",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Inclusive Eligibility Flag": {
                                          "title": "Inclusive Eligibility Flag",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Install Date": {
                                          "title": "Install Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Integration Id": {
                                          "title": "Integration Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Inventory Asset Id": {
                                          "title": "Inventory Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "IsComplexProduct": {
                                          "title": "IsComplexProduct",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Item Price List Id": {
                                          "title": "Item Price List Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Member Asset Id": {
                                          "title": "Member Asset Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Node": {
                                          "title": "Node",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Order Type": {
                                          "title": "Order Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Override Reprice Flag": {
                                          "title": "Override Reprice Flag",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Owner Account Id": {
                                          "title": "Owner Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Owner Type Code": {
                                          "title": "Owner Type Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "75",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Parent Id": {
                                          "title": "Parent Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Policy Discount Amount": {
                                          "title": "Policy Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Port Item Id": {
                                          "title": "Port Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Port Number": {
                                          "title": "Port Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Post Pick CD": {
                                          "title": "Post Pick CD",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Pre Pick CD": {
                                          "title": "Pre Pick CD",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Pre Pick Mode": {
                                          "title": "Pre Pick Mode",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prefix": {
                                          "title": "Prefix",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Previous Asset Status": {
                                          "title": "Previous Asset Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Previous Billing Account Id": {
                                          "title": "Previous Billing Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Previous Billing Profile Id": {
                                          "title": "Previous Billing Profile Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Previous Net Price": {
                                          "title": "Previous Net Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Previous Service Account Id": {
                                          "title": "Previous Service Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Previous Service Id": {
                                          "title": "Previous Service Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Previous Usage Asset Id": {
                                          "title": "Previous Usage Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Price Type": {
                                          "title": "Price Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prior End Date": {
                                          "title": "Prior End Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Processed Flag": {
                                          "title": "Processed Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prod Item Id": {
                                          "title": "Prod Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Id": {
                                          "title": "Prod Prom Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Instance Id": {
                                          "title": "Prod Prom Instance Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Rule Id": {
                                          "title": "Prod Prom Rule Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Source Id": {
                                          "title": "Prod Prom Source Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Product Description": {
                                          "title": "Product Description",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Line Id": {
                                          "title": "Product Line Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Product Primary Product Line Id": {
                                          "title": "Product Primary Product Line Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Product Type": {
                                          "title": "Product Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Type Code": {
                                          "title": "Product Type Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product XA Class Id": {
                                          "title": "Product XA Class Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prom Group Commitment Covered Flag": {
                                          "title": "Prom Group Commitment Covered Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Convert To Agreement Flag": {
                                          "title": "Prom Group Convert To Agreement Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Convert To Asset Flag": {
                                          "title": "Prom Group Convert To Asset Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Id": {
                                          "title": "Prom Group Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prom Group Instance Id": {
                                          "title": "Prom Group Instance Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Rule Id": {
                                          "title": "Prom Group Rule Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Promotion Convert To Agreement Flag": {
                                          "title": "Promotion Convert To Agreement Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Convert To Asset Flag": {
                                          "title": "Promotion Convert To Asset Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Item Flag": {
                                          "title": "Promotion Item Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Operation Id": {
                                          "title": "Promotion Operation Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Operation Type": {
                                          "title": "Promotion Operation Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Upgrade Path Id": {
                                          "title": "Promotion Upgrade Path Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Quote Item Id": {
                                          "title": "Quote Item Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Related Asset Integration Id": {
                                          "title": "Related Asset Integration Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Related Product Id": {
                                          "title": "Related Product Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Requested Porting Date": {
                                          "title": "Requested Porting Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Revised Line Item Id": {
                                          "title": "Revised Line Item Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Rollup Amount": {
                                          "title": "Rollup Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Rollup Item Price": {
                                          "title": "Rollup Item Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Root Account Id": {
                                          "title": "Root Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Integration Id": {
                                          "title": "Root Integration Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Root Prod Prom Instance Id": {
                                          "title": "Root Prod Prom Instance Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Row Id": {
                                          "title": "Row Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Score": {
                                          "title": "Score",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Service Account Id": {
                                          "title": "Service Account Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Service Address Id": {
                                          "title": "Service Address Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Service End Date": {
                                          "title": "Service End Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Service Id": {
                                          "title": "Service Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Instance": {
                                          "title": "Service Instance",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Service Length": {
                                          "title": "Service Length",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Service Length UoM": {
                                          "title": "Service Length UoM",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Start Date": {
                                          "title": "Service Start Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Service Type": {
                                          "title": "Service Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Ship To Address Id": {
                                          "title": "Ship To Address Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Special Rating List Id": {
                                          "title": "Special Rating List Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Status": {
                                          "title": "Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Sub-Action Code": {
                                          "title": "Sub-Action Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Tax Exempt Flag": {
                                          "title": "Tax Exempt Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Tier Price Info": {
                                          "title": "Tier Price Info",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To CLLI": {
                                          "title": "To CLLI",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Node": {
                                          "title": "To Node",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Port Number": {
                                          "title": "To Port Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Prefix": {
                                          "title": "To Prefix",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Service Account Id": {
                                          "title": "To Service Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "To Service Address Id": {
                                          "title": "To Service Address Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "To Service Point Id": {
                                          "title": "To Service Point Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Unit of Measure": {
                                          "title": "Unit of Measure",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Usage Asset Id": {
                                          "title": "Usage Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Discount Id": {
                                          "title": "Volume Discount Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Discount Item Id": {
                                          "title": "Volume Discount Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Upsell Item Id": {
                                          "title": "Volume Upsell Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Upsell Message": {
                                          "title": "Volume Upsell Message",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "250",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Write-In Product Name": {
                                          "title": "Write-In Product Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Def Type Code": {
                                          "title": "Product Def Type Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Root Action Code": {
                                          "title": "Root Action Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "ListOfXA": {
                                          "type": "object",
                                          "properties": {
                                            "XA": {
                                              "type": "array",
                                              "items": {
                                                "type": "object",
                                                "properties": {
                                                  "Conflict Id": {
                                                    "title": "Conflict Id",
                                                    "type": "string",
                                                    "x-maxLength": "30",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  },
                                                  "Created": {
                                                    "title": "Created",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_DATETIME"
                                                  },
                                                  "Id": {
                                                    "title": "Id",
                                                    "type": "string",
                                                    "x-maxLength": "30",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  },
                                                  "LOV Type": {
                                                    "title": "LOV Type",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Previous Value": {
                                                    "title": "Previous Value",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "100",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Property Type Code": {
                                                    "title": "Property Type Code",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Updated": {
                                                    "title": "Updated",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_DATETIME"
                                                  },
                                                  "Validation": {
                                                    "title": "Validation",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "250",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Value": {
                                                    "title": "Value",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "100",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Action Code": {
                                                    "title": "Action Code",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Cfg State Code": {
                                                    "title": "Cfg State Code",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Description": {
                                                    "title": "Description",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "250",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Display Name": {
                                                    "title": "Display Name",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "100",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Hidden": {
                                                    "title": "Hidden",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "1",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "MLOV": {
                                                    "title": "MLOV",
                                                    "type": "string",
                                                    "x-maxLength": "1",
                                                    "x-siebel-datatype": "DTYPE_BOOL"
                                                  },
                                                  "Name": {
                                                    "title": "Name",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "75",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Parent Id": {
                                                    "title": "Parent Id",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  },
                                                  "Read Only": {
                                                    "title": "Read Only",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "1",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Required": {
                                                    "title": "Required",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "1",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Sequence": {
                                                    "title": "Sequence",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "0",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_INTEGER"
                                                  },
                                                  "Unit of Measure": {
                                                    "title": "Unit of Measure",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "XA Id": {
                                                    "title": "XA Id",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        },
                                        "ListOfDeleted Item": {
                                          "type": "object",
                                          "properties": {
                                            "Deleted Item": {
                                              "type": "array",
                                              "items": {
                                                "type": "object",
                                                "properties": {
                                                  "Port Id": {
                                                    "title": "Port Id",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Product Id": {
                                                    "title": "Product Id",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  "x-siebel-datatype": "Integration Object"
                },
                "ERR": {
                  "title": "ERR",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "Success": {
                  "title": "Success",
                  "type": "string",
                  "x-siebel-datatype": "String"
                }
              }
            }
          },
          "application/xml": {
            "schema": {
              "type": "object",
              "properties": {
                "OrderId": {
                  "title": "OrderId",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "PromotionRuleId": {
                  "title": "PromotionRuleId",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "PromotionId": {
                  "title": "PromotionId",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "PromotionRoots": {
                  "title": "PromotionRoots",
                  "type": "object",
                  "properties": {
                    "MessageId": {
                      "type": "string",
                      "example": ""
                    },
                    "MessageType": {
                      "type": "string",
                      "example": "Integration Object"
                    },
                    "IntObjectName": {
                      "type": "string",
                      "example": "SIS OM Order"
                    },
                    "IntObjectFormat": {
                      "type": "string",
                      "example": "Siebel Hierarchical"
                    },
                    "ListOfSIS OM Order": {
                      "type": "object",
                      "properties": {
                        "Header": {
                          "minItems": 1,
                          "type": "array",
                          "items": {
                            "type": "object",
                            "properties": {
                              "Account": {
                                "title": "Account",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "100",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Account Location": {
                                "title": "Account Location",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "50",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "City": {
                                "title": "City",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Conflict Id": {
                                "title": "Conflict Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Country": {
                                "title": "Country",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Created": {
                                "title": "Created",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_DATETIME"
                              },
                              "Discount": {
                                "title": "Discount",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_NUMBER"
                              },
                              "Id": {
                                "title": "Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Name": {
                                "title": "Name",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "75",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Postal Code": {
                                "title": "Postal Code",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "State": {
                                "title": "State",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Updated": {
                                "title": "Updated",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_DATETIME"
                              },
                              "Account Id": {
                                "title": "Account Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Account Type": {
                                "title": "Account Type",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Active": {
                                "title": "Active",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_BOOL"
                              },
                              "Agreement Id": {
                                "title": "Agreement Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Applicant Group Id": {
                                "title": "Applicant Group Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "As Of Date": {
                                "title": "As Of Date",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_UTCDATETIME"
                              },
                              "Billing Account Id": {
                                "title": "Billing Account Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Billing Profile Id": {
                                "title": "Billing Profile Id",
                                "type": "string",
                                "x-maxLength": "15",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Compound Product Number": {
                                "title": "Compound Product Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "100",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Contact Id": {
                                "title": "Contact Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Currency Code": {
                                "title": "Currency Code",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Discount Amount": {
                                "title": "Discount Amount",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Discount Amount MRC": {
                                "title": "Discount Amount MRC",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Discount Reason": {
                                "title": "Discount Reason",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "250",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Freight": {
                                "title": "Freight",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Integration Id": {
                                "title": "Integration Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Opportunity Id": {
                                "title": "Opportunity Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Order Number": {
                                "title": "Order Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Order Type": {
                                "title": "Order Type",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Pre Pick Mode": {
                                "title": "Pre Pick Mode",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Price List Id": {
                                "title": "Price List Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Quote Id": {
                                "title": "Quote Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Quote Number": {
                                "title": "Quote Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "75",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Requested Ship Date": {
                                "title": "Requested Ship Date",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_DATETIME"
                              },
                              "Revision Number": {
                                "title": "Revision Number",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_NUMBER"
                              },
                              "Service Account Id": {
                                "title": "Service Account Id",
                                "type": "string",
                                "x-maxLength": "30",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Ship To Account Id": {
                                "title": "Ship To Account Id",
                                "type": "string",
                                "x-maxLength": "15",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Ship To Address Id": {
                                "title": "Ship To Address Id",
                                "type": "string",
                                "x-maxLength": "15",
                                "x-siebel-datatype": "DTYPE_ID"
                              },
                              "Status": {
                                "title": "Status",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "30",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "Tax Amount": {
                                "title": "Tax Amount",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_CURRENCY"
                              },
                              "Tax Exempt": {
                                "title": "Tax Exempt",
                                "type": "string",
                                "x-maxLength": "0",
                                "x-siebel-datatype": "DTYPE_BOOL"
                              },
                              "Tax Rate": {
                                "title": "Tax Rate",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "0",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_NUMBER"
                              },
                              "Price List": {
                                "title": "Price List",
                                "type": "string",
                                "x-siebel-precision": "0",
                                "x-maxLength": "100",
                                "x-siebel-scale": "0",
                                "x-siebel-datatype": "DTYPE_TEXT"
                              },
                              "ListOfLine Item": {
                                "type": "object",
                                "properties": {
                                  "Line Item": {
                                    "type": "array",
                                    "items": {
                                      "type": "object",
                                      "properties": {
                                        "Action Code": {
                                          "title": "Action Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Adjusted List Price": {
                                          "title": "Adjusted List Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Asset Status": {
                                          "title": "Asset Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Base Price": {
                                          "title": "Base Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Billing Account": {
                                          "title": "Billing Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Billing Type": {
                                          "title": "Billing Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Calc Discount Amount": {
                                          "title": "Calc Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Calc Discount Percent": {
                                          "title": "Calc Discount Percent",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Calculated Asset Status": {
                                          "title": "Calculated Asset Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Calculated Due Date": {
                                          "title": "Calculated Due Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "City": {
                                          "title": "City",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Class Id": {
                                          "title": "Class Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Configuration Model Id": {
                                          "title": "Configuration Model Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Conflict Id": {
                                          "title": "Conflict Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Country": {
                                          "title": "Country",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Created": {
                                          "title": "Created",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Currency Code": {
                                          "title": "Currency Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "15",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Discount": {
                                          "title": "Discount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Discount Amount": {
                                          "title": "Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Discount Amount MRC": {
                                          "title": "Discount Amount MRC",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Discount Percent": {
                                          "title": "Discount Percent",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Discount Percent MRC": {
                                          "title": "Discount Percent MRC",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Discount Source": {
                                          "title": "Discount Source",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Donating Service Provider": {
                                          "title": "Donating Service Provider",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Dynamic Discount Method": {
                                          "title": "Dynamic Discount Method",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Effective End Date": {
                                          "title": "Effective End Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Effective Start Date": {
                                          "title": "Effective Start Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Ending Phone Number": {
                                          "title": "Ending Phone Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "20",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Exclude Pricing Flag": {
                                          "title": "Exclude Pricing Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Forcastable Flag": {
                                          "title": "Forcastable Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Has Generics Flag": {
                                          "title": "Has Generics Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Header Discount Amount": {
                                          "title": "Header Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Header Id": {
                                          "title": "Header Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Id": {
                                          "title": "Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Legacy Account Number": {
                                          "title": "Legacy Account Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "List Price": {
                                          "title": "List Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "MRC CxTotal": {
                                          "title": "MRC CxTotal",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "MRC Search Spec": {
                                          "title": "MRC Search Spec",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Max Price": {
                                          "title": "Max Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Min Price": {
                                          "title": "Min Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "NRC CxTotal": {
                                          "title": "NRC CxTotal",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "NRC Search Spec": {
                                          "title": "NRC Search Spec",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Name": {
                                          "title": "Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Need Refresh": {
                                          "title": "Need Refresh",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Net Price": {
                                          "title": "Net Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Network Element Type": {
                                          "title": "Network Element Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Number Portability Agency Name": {
                                          "title": "Number Portability Agency Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Number To Port": {
                                          "title": "Number To Port",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "20",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Original List Price": {
                                          "title": "Original List Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Original Order Id": {
                                          "title": "Original Order Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Owner Account": {
                                          "title": "Owner Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "PIN": {
                                          "title": "PIN",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Postal Code": {
                                          "title": "Postal Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Price List Id": {
                                          "title": "Price List Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Pricing Adjustment Amount": {
                                          "title": "Pricing Adjustment Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Pricing Comments": {
                                          "title": "Pricing Comments",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "250",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Pricing Commit Type": {
                                          "title": "Pricing Commit Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prod Prom Name": {
                                          "title": "Prod Prom Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prod Prom Type": {
                                          "title": "Prod Prom Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product": {
                                          "title": "Product",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Id": {
                                          "title": "Product Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prom Group Name": {
                                          "title": "Prom Group Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Rule Type": {
                                          "title": "Prom Group Rule Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Quantity": {
                                          "title": "Quantity",
                                          "type": "string",
                                          "x-siebel-precision": "16",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_INTEGER"
                                        },
                                        "Root Id": {
                                          "title": "Root Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Product Id": {
                                          "title": "Root Product Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Promotion Group Id": {
                                          "title": "Root Promotion Group Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Promotion Id": {
                                          "title": "Root Promotion Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Sequence Number": {
                                          "title": "Sequence Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_INTEGER"
                                        },
                                        "Service Account": {
                                          "title": "Service Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Address": {
                                          "title": "Service Address",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Point Id": {
                                          "title": "Service Point Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Service Postal Code": {
                                          "title": "Service Postal Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Price Method": {
                                          "title": "Service Price Method",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Price Percent": {
                                          "title": "Service Price Percent",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Smart Part Number": {
                                          "title": "Smart Part Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "250",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Starting Phone Number": {
                                          "title": "Starting Phone Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "20",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "State": {
                                          "title": "State",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Tax Amount": {
                                          "title": "Tax Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Tier Price Flag": {
                                          "title": "Tier Price Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Service Account": {
                                          "title": "To Service Account",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Unit Price": {
                                          "title": "Unit Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Updated": {
                                          "title": "Updated",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Volume Discount Item": {
                                          "title": "Volume Discount Item",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Volume Upsell Item": {
                                          "title": "Volume Upsell Item",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "50",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Account Id": {
                                          "title": "Account Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Account Type": {
                                          "title": "Account Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Agreement Id": {
                                          "title": "Agreement Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Applicant Group Id": {
                                          "title": "Applicant Group Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Asset Integration Id": {
                                          "title": "Asset Integration Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Asset Member Compatibility": {
                                          "title": "Asset Member Compatibility",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Asset Number": {
                                          "title": "Asset Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Auto Explode Flag": {
                                          "title": "Auto Explode Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Base Line Item Id": {
                                          "title": "Base Line Item Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Billing Account Id": {
                                          "title": "Billing Account Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Billing Profile Id": {
                                          "title": "Billing Profile Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Billing Profile Name": {
                                          "title": "Billing Profile Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "CLLI": {
                                          "title": "CLLI",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cfg Latest Released Flag": {
                                          "title": "Cfg Latest Released Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cfg State Code": {
                                          "title": "Cfg State Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cfg Type": {
                                          "title": "Cfg Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Change Cost": {
                                          "title": "Change Cost",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Commitment Covered Flag": {
                                          "title": "Commitment Covered Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Compound Product Flag": {
                                          "title": "Compound Product Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Compound Product Number": {
                                          "title": "Compound Product Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Contact Id": {
                                          "title": "Contact Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Convert To Agreement Flag": {
                                          "title": "Convert To Agreement Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Convert To Asset Flag": {
                                          "title": "Convert To Asset Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Cost": {
                                          "title": "Cost",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Covered Asset Id": {
                                          "title": "Covered Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Current Price": {
                                          "title": "Current Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Deleted Products": {
                                          "title": "Deleted Products",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1000",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Depends on Id": {
                                          "title": "Depends on Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Description": {
                                          "title": "Description",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Due Date": {
                                          "title": "Due Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Effective From": {
                                          "title": "Effective From",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Effective To": {
                                          "title": "Effective To",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Eligibility Reason": {
                                          "title": "Eligibility Reason",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "500",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Eligibility Status": {
                                          "title": "Eligibility Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Exchange Date": {
                                          "title": "Exchange Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Extended Quantity": {
                                          "title": "Extended Quantity",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Extended Quantity Requested": {
                                          "title": "Extended Quantity Requested",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Inclusive Eligibility Flag": {
                                          "title": "Inclusive Eligibility Flag",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Install Date": {
                                          "title": "Install Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATETIME"
                                        },
                                        "Integration Id": {
                                          "title": "Integration Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Inventory Asset Id": {
                                          "title": "Inventory Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "IsComplexProduct": {
                                          "title": "IsComplexProduct",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Item Price List Id": {
                                          "title": "Item Price List Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Member Asset Id": {
                                          "title": "Member Asset Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Node": {
                                          "title": "Node",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Order Type": {
                                          "title": "Order Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Override Reprice Flag": {
                                          "title": "Override Reprice Flag",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Owner Account Id": {
                                          "title": "Owner Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Owner Type Code": {
                                          "title": "Owner Type Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "75",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Parent Id": {
                                          "title": "Parent Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Policy Discount Amount": {
                                          "title": "Policy Discount Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Port Item Id": {
                                          "title": "Port Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Port Number": {
                                          "title": "Port Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Post Pick CD": {
                                          "title": "Post Pick CD",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Pre Pick CD": {
                                          "title": "Pre Pick CD",
                                          "type": "string",
                                          "x-maxLength": "1",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Pre Pick Mode": {
                                          "title": "Pre Pick Mode",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prefix": {
                                          "title": "Prefix",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Previous Asset Status": {
                                          "title": "Previous Asset Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Previous Billing Account Id": {
                                          "title": "Previous Billing Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Previous Billing Profile Id": {
                                          "title": "Previous Billing Profile Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Previous Net Price": {
                                          "title": "Previous Net Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Previous Service Account Id": {
                                          "title": "Previous Service Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Previous Service Id": {
                                          "title": "Previous Service Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Previous Usage Asset Id": {
                                          "title": "Previous Usage Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Price Type": {
                                          "title": "Price Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prior End Date": {
                                          "title": "Prior End Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_DATE"
                                        },
                                        "Processed Flag": {
                                          "title": "Processed Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prod Item Id": {
                                          "title": "Prod Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Id": {
                                          "title": "Prod Prom Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Instance Id": {
                                          "title": "Prod Prom Instance Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Rule Id": {
                                          "title": "Prod Prom Rule Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prod Prom Source Id": {
                                          "title": "Prod Prom Source Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Product Description": {
                                          "title": "Product Description",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Line Id": {
                                          "title": "Product Line Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Product Primary Product Line Id": {
                                          "title": "Product Primary Product Line Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Product Type": {
                                          "title": "Product Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Type Code": {
                                          "title": "Product Type Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product XA Class Id": {
                                          "title": "Product XA Class Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prom Group Commitment Covered Flag": {
                                          "title": "Prom Group Commitment Covered Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Convert To Agreement Flag": {
                                          "title": "Prom Group Convert To Agreement Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Convert To Asset Flag": {
                                          "title": "Prom Group Convert To Asset Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Id": {
                                          "title": "Prom Group Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Prom Group Instance Id": {
                                          "title": "Prom Group Instance Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Prom Group Rule Id": {
                                          "title": "Prom Group Rule Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Promotion Convert To Agreement Flag": {
                                          "title": "Promotion Convert To Agreement Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Convert To Asset Flag": {
                                          "title": "Promotion Convert To Asset Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Item Flag": {
                                          "title": "Promotion Item Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "1",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Operation Id": {
                                          "title": "Promotion Operation Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Operation Type": {
                                          "title": "Promotion Operation Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "255",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Promotion Upgrade Path Id": {
                                          "title": "Promotion Upgrade Path Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Quote Item Id": {
                                          "title": "Quote Item Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Related Asset Integration Id": {
                                          "title": "Related Asset Integration Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Related Product Id": {
                                          "title": "Related Product Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Requested Porting Date": {
                                          "title": "Requested Porting Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Revised Line Item Id": {
                                          "title": "Revised Line Item Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Rollup Amount": {
                                          "title": "Rollup Amount",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Rollup Item Price": {
                                          "title": "Rollup Item Price",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_CURRENCY"
                                        },
                                        "Root Account Id": {
                                          "title": "Root Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Root Integration Id": {
                                          "title": "Root Integration Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Root Prod Prom Instance Id": {
                                          "title": "Root Prod Prom Instance Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Row Id": {
                                          "title": "Row Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Score": {
                                          "title": "Score",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Service Account Id": {
                                          "title": "Service Account Id",
                                          "type": "string",
                                          "x-maxLength": "30",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Service Address Id": {
                                          "title": "Service Address Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Service End Date": {
                                          "title": "Service End Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Service Id": {
                                          "title": "Service Id",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Instance": {
                                          "title": "Service Instance",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_BOOL"
                                        },
                                        "Service Length": {
                                          "title": "Service Length",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_NUMBER"
                                        },
                                        "Service Length UoM": {
                                          "title": "Service Length UoM",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Service Start Date": {
                                          "title": "Service Start Date",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_UTCDATETIME"
                                        },
                                        "Service Type": {
                                          "title": "Service Type",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Ship To Address Id": {
                                          "title": "Ship To Address Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Special Rating List Id": {
                                          "title": "Special Rating List Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Status": {
                                          "title": "Status",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Sub-Action Code": {
                                          "title": "Sub-Action Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Tax Exempt Flag": {
                                          "title": "Tax Exempt Flag",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Tier Price Info": {
                                          "title": "Tier Price Info",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To CLLI": {
                                          "title": "To CLLI",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Node": {
                                          "title": "To Node",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Port Number": {
                                          "title": "To Port Number",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Prefix": {
                                          "title": "To Prefix",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "To Service Account Id": {
                                          "title": "To Service Account Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "To Service Address Id": {
                                          "title": "To Service Address Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "To Service Point Id": {
                                          "title": "To Service Point Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Unit of Measure": {
                                          "title": "Unit of Measure",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Usage Asset Id": {
                                          "title": "Usage Asset Id",
                                          "type": "string",
                                          "x-maxLength": "15",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Discount Id": {
                                          "title": "Volume Discount Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Discount Item Id": {
                                          "title": "Volume Discount Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Upsell Item Id": {
                                          "title": "Volume Upsell Item Id",
                                          "type": "string",
                                          "x-maxLength": "0",
                                          "x-siebel-datatype": "DTYPE_ID"
                                        },
                                        "Volume Upsell Message": {
                                          "title": "Volume Upsell Message",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "250",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Write-In Product Name": {
                                          "title": "Write-In Product Name",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "100",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Product Def Type Code": {
                                          "title": "Product Def Type Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "0",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "Root Action Code": {
                                          "title": "Root Action Code",
                                          "type": "string",
                                          "x-siebel-precision": "0",
                                          "x-maxLength": "30",
                                          "x-siebel-scale": "0",
                                          "x-siebel-datatype": "DTYPE_TEXT"
                                        },
                                        "ListOfXA": {
                                          "type": "object",
                                          "properties": {
                                            "XA": {
                                              "type": "array",
                                              "items": {
                                                "type": "object",
                                                "properties": {
                                                  "Conflict Id": {
                                                    "title": "Conflict Id",
                                                    "type": "string",
                                                    "x-maxLength": "30",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  },
                                                  "Created": {
                                                    "title": "Created",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_DATETIME"
                                                  },
                                                  "Id": {
                                                    "title": "Id",
                                                    "type": "string",
                                                    "x-maxLength": "30",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  },
                                                  "LOV Type": {
                                                    "title": "LOV Type",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Previous Value": {
                                                    "title": "Previous Value",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "100",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Property Type Code": {
                                                    "title": "Property Type Code",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Updated": {
                                                    "title": "Updated",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_DATETIME"
                                                  },
                                                  "Validation": {
                                                    "title": "Validation",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "250",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Value": {
                                                    "title": "Value",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "100",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Action Code": {
                                                    "title": "Action Code",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Cfg State Code": {
                                                    "title": "Cfg State Code",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Description": {
                                                    "title": "Description",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "250",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Display Name": {
                                                    "title": "Display Name",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "100",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Hidden": {
                                                    "title": "Hidden",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "1",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "MLOV": {
                                                    "title": "MLOV",
                                                    "type": "string",
                                                    "x-maxLength": "1",
                                                    "x-siebel-datatype": "DTYPE_BOOL"
                                                  },
                                                  "Name": {
                                                    "title": "Name",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "75",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Parent Id": {
                                                    "title": "Parent Id",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  },
                                                  "Read Only": {
                                                    "title": "Read Only",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "1",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Required": {
                                                    "title": "Required",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "1",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Sequence": {
                                                    "title": "Sequence",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "0",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_INTEGER"
                                                  },
                                                  "Unit of Measure": {
                                                    "title": "Unit of Measure",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "XA Id": {
                                                    "title": "XA Id",
                                                    "type": "string",
                                                    "x-maxLength": "0",
                                                    "x-siebel-datatype": "DTYPE_ID"
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        },
                                        "ListOfDeleted Item": {
                                          "type": "object",
                                          "properties": {
                                            "Deleted Item": {
                                              "type": "array",
                                              "items": {
                                                "type": "object",
                                                "properties": {
                                                  "Port Id": {
                                                    "title": "Port Id",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  },
                                                  "Product Id": {
                                                    "title": "Product Id",
                                                    "type": "string",
                                                    "x-siebel-precision": "0",
                                                    "x-maxLength": "30",
                                                    "x-siebel-scale": "0",
                                                    "x-siebel-datatype": "DTYPE_TEXT"
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  "x-siebel-datatype": "Integration Object"
                },
                "ERR": {
                  "title": "ERR",
                  "type": "string",
                  "x-siebel-datatype": "String"
                },
                "Success": {
                  "title": "Success",
                  "type": "string",
                  "x-siebel-datatype": "String"
                }
              }
            }
          }
        }
      },
      "204": {
        "description": "No Resource Found",
        "content": {}
      },
      "304": {
        "description": "Not Modified",
        "content": {}
      },
      "401": {
        "description": "Unauthorized",
        "content": {}
      },
      "403": {
        "description": "Access Forbidden",
        "content": {}
      },
      "404": {
        "description": "Business service or method doesnt exist",
        "content": {}
      },
      "500": {
        "description": "Internal Server Error",
        "content": {}
      }
    },
    "security": [
      {
        "basicAuth": [],
        "oAuth2.0": []
      }
    ],
    "x-codegen-request-body-name": "body"
  },
  "_metadata": {
    "created_at": {
      "$date": "2025-05-22T10:01:06.795Z"
    },
    "modified_at": {
      "$date": "2025-05-22T10:01:19.330Z"
    }
  }
}
```