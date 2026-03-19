package output

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/olekukonko/tablewriter"
	"gopkg.in/yaml.v3"
)

type Format string

const (
	FormatTable Format = "table"
	FormatJSON  Format = "json"
	FormatYAML  Format = "yaml"
)

// Print outputs data in the requested format.
// headers/rows are used for table format; data is used for json/yaml.
func Print(format Format, headers []string, rows [][]string, data any) error {
	switch format {
	case FormatJSON:
		return printJSON(data)
	case FormatYAML:
		return printYAML(data)
	default:
		printTable(headers, rows)
		return nil
	}
}

// PrintOne outputs a single object. For table format, renders as key-value pairs.
func PrintOne(format Format, data map[string]any) error {
	switch format {
	case FormatJSON:
		return printJSON(data)
	case FormatYAML:
		return printYAML(data)
	default:
		t := tablewriter.NewWriter(os.Stdout)
		t.SetHeader([]string{"FIELD", "VALUE"})
		t.SetBorder(false)
		t.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
		t.SetAlignment(tablewriter.ALIGN_LEFT)
		t.SetColWidth(80)
		for k, v := range data {
			t.Append([]string{k, fmt.Sprintf("%v", v)})
		}
		t.Render()
		return nil
	}
}

func printTable(headers []string, rows [][]string) {
	t := tablewriter.NewWriter(os.Stdout)
	t.SetHeader(headers)
	t.SetBorder(false)
	t.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
	t.SetAlignment(tablewriter.ALIGN_LEFT)
	t.SetColWidth(60)
	t.AppendBulk(rows)
	t.Render()
}

func printJSON(data any) error {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(data)
}

func printYAML(data any) error {
	b, err := yaml.Marshal(data)
	if err != nil {
		return err
	}
	fmt.Print(string(b))
	return nil
}
