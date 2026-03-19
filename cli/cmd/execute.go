package cmd

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"magnet-ai/cli/internal/client"
	"magnet-ai/cli/internal/config"
	"magnet-ai/cli/internal/output"

	"github.com/spf13/cobra"
)

var executeCmd = &cobra.Command{
	Use:   "execute",
	Short: "Execute an agent with a message (single turn)",
	Long: `Send a single message to an agent and receive a response.

Creates a conversation, sends the message, and prints the response.
If --message is not provided, reads from stdin.

Examples:
  magnet execute --agent my-agent --message "Summarize our Q4 results"
  echo "What is the capital of France?" | magnet execute --agent my-agent
  magnet execute --agent my-agent --message "Hello" --output json`,
	RunE: func(cmd *cobra.Command, args []string) error {
		agentSystemName, _ := cmd.Flags().GetString("agent")
		message, _ := cmd.Flags().GetString("message")

		// Read message from stdin if not provided via flag
		if message == "" {
			stat, _ := os.Stdin.Stat()
			if (stat.Mode() & os.ModeCharDevice) == 0 {
				data, err := io.ReadAll(os.Stdin)
				if err != nil {
					return fmt.Errorf("failed to read stdin: %w", err)
				}
				message = strings.TrimSpace(string(data))
			}
		}
		if message == "" {
			return fmt.Errorf("--message is required (or pipe message via stdin)")
		}

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		// Create conversation with the initial message
		body := map[string]any{
			"agent":                agentSystemName,
			"user_message_content": message,
		}

		var result map[string]any
		if err := c.Create("/api/user/agent_conversations", body, &result); err != nil {
			return err
		}

		// Pretty-print the response content if in table mode
		if outputFormat() == string(output.FormatTable) {
			if content, ok := extractAssistantContent(result); ok {
				fmt.Println(content)
				return nil
			}
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

// extractAssistantContent pulls the assistant reply text from a conversation response.
func extractAssistantContent(result map[string]any) (string, bool) {
	// Try result.messages[] → last assistant message
	if messages, ok := result["messages"].([]any); ok {
		for i := len(messages) - 1; i >= 0; i-- {
			if msg, ok := messages[i].(map[string]any); ok {
				role, _ := msg["role"].(string)
				if role == "assistant" {
					if content, ok := msg["content"].(string); ok && content != "" {
						return content, true
					}
				}
			}
		}
	}
	// Try result.last_message
	if lm, ok := result["last_message"].(map[string]any); ok {
		if content, ok := lm["content"].(string); ok {
			return content, true
		}
	}
	// Try result.content directly
	if content, ok := result["content"].(string); ok {
		return content, true
	}
	return "", false
}

var chatCmd = &cobra.Command{
	Use:   "chat",
	Short: "Start an interactive chat with an agent",
	Long: `Start an interactive REPL session with an agent.

Type your message and press Enter. Type 'exit' or 'quit' to end the session.

Example:
  magnet chat --agent my-agent`,
	RunE: func(cmd *cobra.Command, args []string) error {
		agentSystemName, _ := cmd.Flags().GetString("agent")

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		fmt.Printf("Starting chat with agent: %s\n", agentSystemName)
		fmt.Println("Type 'exit' or 'quit' to end the session.")
		fmt.Println(strings.Repeat("─", 60))

		var convID string

		scanner := bufio.NewScanner(os.Stdin)
		for {
			fmt.Print("\nYou: ")
			if !scanner.Scan() {
				break
			}
			userInput := strings.TrimSpace(scanner.Text())
			if userInput == "" {
				continue
			}
			if userInput == "exit" || userInput == "quit" {
				fmt.Println("Goodbye!")
				break
			}

			var result map[string]any
			var reqErr error

			if convID == "" {
				// First message: create conversation
				body := map[string]any{
					"agent":                agentSystemName,
					"user_message_content": userInput,
				}
				reqErr = c.Create("/api/user/agent_conversations", body, &result)
				if reqErr == nil {
					if id, ok := result["id"].(string); ok {
						convID = id
					}
				}
			} else {
				// Continue conversation
				body := map[string]any{
					"user_message_content": userInput,
				}
				reqErr = c.Create("/api/user/agent_conversations/"+convID+"/messages", body, &result)
			}

			if reqErr != nil {
				fmt.Fprintf(os.Stderr, "Error: %v\n", reqErr)
				continue
			}

			fmt.Print("\nAssistant: ")
			if content, ok := extractAssistantContent(result); ok {
				fmt.Println(content)
			} else {
				enc := json.NewEncoder(os.Stdout)
				enc.SetIndent("", "  ")
				_ = enc.Encode(result)
			}
		}
		return nil
	},
}

func init() {
	executeCmd.Flags().StringP("agent", "a", "", "Agent system name (required)")
	executeCmd.Flags().StringP("message", "m", "", "Message to send (reads from stdin if omitted)")
	executeCmd.MarkFlagRequired("agent") //nolint:errcheck

	chatCmd.Flags().StringP("agent", "a", "", "Agent system name (required)")
	chatCmd.MarkFlagRequired("agent") //nolint:errcheck

	rootCmd.AddCommand(executeCmd)
	rootCmd.AddCommand(chatCmd)
}
