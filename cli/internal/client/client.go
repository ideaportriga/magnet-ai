package client

import (
	"fmt"
	"io"
	"net/http"

	"magnet-ai/cli/internal/config"

	"github.com/go-resty/resty/v2"
)

type Client struct {
	r       *resty.Client
	BaseURL string
}

func New(cfg *config.Config) *Client {
	r := resty.New().
		SetBaseURL(cfg.BaseURL).
		SetHeader("x-api-key", cfg.APIKey).
		SetHeader("Content-Type", "application/json")
	return &Client{r: r, BaseURL: cfg.BaseURL}
}

// List performs GET with query params and decodes paginated response.
func (c *Client) List(path string, params map[string]string, out any) error {
	resp, err := c.r.R().SetQueryParams(params).SetResult(out).Get(path)
	return checkResp(resp, err)
}

// Get performs GET and decodes result.
func (c *Client) Get(path string, out any) error {
	resp, err := c.r.R().SetResult(out).Get(path)
	return checkResp(resp, err)
}

// Create performs POST with JSON body.
func (c *Client) Create(path string, body any, out any) error {
	resp, err := c.r.R().SetBody(body).SetResult(out).Post(path)
	return checkResp(resp, err)
}

// Update performs PATCH with JSON body.
func (c *Client) Update(path string, body any, out any) error {
	resp, err := c.r.R().SetBody(body).SetResult(out).Patch(path)
	return checkResp(resp, err)
}

// Delete performs DELETE.
func (c *Client) Delete(path string) error {
	resp, err := c.r.R().Delete(path)
	return checkResp(resp, err)
}

// PostRaw performs a POST and returns the raw response body (for streaming/execute).
func (c *Client) PostRaw(path string, body any) (io.ReadCloser, error) {
	req, err := http.NewRequest(http.MethodPost, c.BaseURL+path, nil)
	if err != nil {
		return nil, err
	}
	// Use resty to build URL but raw http for streaming
	resp, err := c.r.R().SetBody(body).SetDoNotParseResponse(true).Post(path)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	if resp.IsError() {
		_ = resp.RawBody().Close()
		return nil, fmt.Errorf("API error %d: %s", resp.StatusCode(), resp.String())
	}
	_ = req // suppress unused warning
	return resp.RawBody(), nil
}

func checkResp(resp *resty.Response, err error) error {
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	if resp.IsError() {
		return fmt.Errorf("API error %d: %s", resp.StatusCode(), resp.String())
	}
	return nil
}
