from logging import getLogger
from typing import Any, Optional, Union

from type_defs.pagination import FilterObject

logger = getLogger(__name__)


class OracleMetadataFilterBuilder:
    OPERATOR_MAP = {
        "$eq": "==",
        "$ne": "!=",
        "$gt": ">",
        "$gte": ">=",
        "$lt": "<",
        "$lte": "<=",
    }

    def _format_value(self, value: Any) -> str:
        if isinstance(value, str):
            # Escape any double quotes within the string itself
            escaped_value = value.replace('"', '\\"')
            return f'"{escaped_value}"'
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return "null"

        raise TypeError(f"Unsupported value type: {type(value)}")

    def _parse_node(
        self, node: Union[dict, list], field_mapping: dict[str, str]
    ) -> str:
        """
        Recursively parses a node in the filter object to build a condition string.
        A node can be a logical operator ($and, $or) or a field condition.
        """
        if not isinstance(node, dict) or len(node) != 1:
            raise ValueError(f"Invalid filter node format: {node}")

        operator = list(node.keys())[0]
        value = node[operator]

        # Case 1: Logical operators ($and, $or)
        if operator in ("$and", "$or"):
            if not isinstance(value, list) or not value:
                raise ValueError(f"Value for {operator} must be a non-empty list.")

            joiner = " && " if operator == "$and" else " || "
            # Recursively parse each sub-node in the list
            sub_clauses = [
                self._parse_node(sub_node, field_mapping) for sub_node in value
            ]
            # Join sub-clauses and wrap in parentheses for correct precedence
            return f"({joiner.join(sub_clauses)})"

        # Case 2: Field condition (e.g., {"field_name": {"$eq": "value"}})
        # At this point, the 'operator' is actually the field name.
        field = operator
        expression = value
        json_path = field_mapping.get(field, field)

        if not isinstance(expression, dict) or len(expression) != 1:
            raise ValueError(
                f"Invalid expression format for field '{field}': {expression}"
            )

        op = list(expression.keys())[0]
        val = expression[op]

        if op == "$exists":
            if not isinstance(val, bool):
                raise ValueError(
                    f"Value for $exists must be a boolean for field '{field}'"
                )
            base_expression = f"exists(@.{json_path})"
            return base_expression if val else f"!({base_expression})"

        if op == "$in":
            if not isinstance(val, list):
                raise ValueError(f"Value for $in must be a list for field '{field}'")
            if not val:  # Handle empty list for $in
                return "1 == 0"  # Always false
            sub_clauses = [
                f"@.{json_path} == {self._format_value(item)}" for item in val
            ]
            return f"({' || '.join(sub_clauses)})"

        if op == "$nin":
            if not isinstance(val, list):
                raise ValueError(f"Value for $nin must be a list for field '{field}'")
            if not val:  # Handle empty list for $nin
                return "1 == 1"  # Always true
            sub_clauses = [
                f"@.{json_path} != {self._format_value(item)}" for item in val
            ]
            return f"({' && '.join(sub_clauses)})"

        # Handle simple comparison operators
        try:
            sql_operator = self.OPERATOR_MAP[op]
            formatted_value = self._format_value(val)
            return f"@.{json_path} {sql_operator} {formatted_value}"
        except KeyError:
            raise ValueError(f"Unsupported operator: {op}")

    def build(self, collection_config: dict, filter: Optional[FilterObject]) -> str:
        """
        Builds the complete 'JSON_EXISTS(...)' clause from a filter object.

        Args:
            collection_config: Configuration containing the metadata field mappings.
            filter: The filter object to build the clause from.

        Returns:
            A JSON_EXISTS clause string, or an empty string if the filter is empty.
        """
        if not filter:
            return ""

        filter_dict = filter.model_dump(exclude_none=True, by_alias=True)

        if not filter_dict:
            return ""

        field_mapping: dict[str, str] = {}
        metadata_config = (
            collection_config.get("metadata_config") if collection_config else None
        )
        if isinstance(metadata_config, list):
            for item in metadata_config:
                if item.get("enabled") and item.get("name") and item.get("mapping"):
                    path = item["mapping"]
                    # Strip '$.' prefix to get the relative path for the '@' context
                    if path.startswith("$."):
                        path = path[2:]
                    field_mapping[item["name"]] = path

        try:
            # Start the recursive parsing from the root of the filter object
            full_expression = self._parse_node(filter_dict, field_mapping)
            # The recursive parser adds its own parentheses, so we can remove the outer ones
            # if they exist to avoid doubling up, e.g. ((...))
            if full_expression.startswith("(") and full_expression.endswith(")"):
                full_expression = full_expression[1:-1]

        except Exception as e:
            logger.error(f"Error parsing filter object: {e}")
            raise e

        # Construct the final SQL clause
        return f"JSON_EXISTS(metadata, '$?({full_expression})')"
