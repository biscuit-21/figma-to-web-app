// Command key-indicators serves the U.S. economic indicators dashboard from a
// single self-contained executable. The dashboard is compiled into the binary,
// so there is nothing to install and nothing to fetch at runtime.
package main

import (
	"embed"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"runtime"
	"syscall"
	"time"
)

//go:embed all:web
var assets embed.FS

var version = "dev" // overridden at build time with -ldflags

func main() {
	port := flag.Int("port", 7331, "port to listen on; 0 picks any free port")
	host := flag.String("host", "127.0.0.1", "address to bind; use 0.0.0.0 to expose on your network")
	open := flag.Bool("open", true, "open the dashboard in your browser on start")
	showVersion := flag.Bool("version", false, "print the version and exit")
	flag.Parse()

	if *showVersion {
		fmt.Println("key-indicators", version)
		return
	}

	site, err := fs.Sub(assets, "web")
	if err != nil {
		log.Fatalf("embedded assets are unreadable: %v", err)
	}

	addr := net.JoinHostPort(*host, fmt.Sprint(*port))
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		log.Fatalf("cannot listen on %s: %v\nAnother program may already be using that port. Try -port 0.", addr, err)
	}

	url := "http://" + ln.Addr().String()
	fmt.Printf("Key Indicators %s\n", version)
	fmt.Printf("Serving at %s\n", url)
	fmt.Println("Press Ctrl+C to stop.")

	if *open {
		go func() {
			time.Sleep(250 * time.Millisecond)
			openBrowser(url)
		}()
	}

	srv := &http.Server{
		Handler:           withHeaders(http.FileServer(http.FS(site))),
		ReadHeaderTimeout: 10 * time.Second,
	}

	go func() {
		stop := make(chan os.Signal, 1)
		signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
		<-stop
		fmt.Println("\nStopping.")
		_ = srv.Close()
	}()

	if err := srv.Serve(ln); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
}

// withHeaders sets a content security policy matching what the page actually
// needs: its own inline styles and script, plus Google Fonts. No other origin
// is reachable, and the page makes no network calls of its own.
func withHeaders(next http.Handler) http.Handler {
	const csp = "default-src 'none'; " +
		"script-src 'unsafe-inline'; " +
		"style-src 'unsafe-inline' https://fonts.googleapis.com; " +
		"font-src https://fonts.gstatic.com; " +
		"img-src 'self' data:; " +
		"connect-src 'none'; " +
		"base-uri 'none'; " +
		"form-action 'none'; " +
		"frame-ancestors 'none'"
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", csp)
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		next.ServeHTTP(w, r)
	})
}

func openBrowser(url string) {
	var cmd string
	var args []string
	switch runtime.GOOS {
	case "darwin":
		cmd = "open"
	case "windows":
		cmd, args = "rundll32", []string{"url.dll,FileProtocolHandler"}
	default:
		cmd = "xdg-open"
	}
	if err := exec.Command(cmd, append(args, url)...).Start(); err != nil {
		fmt.Println("Could not open a browser automatically. Visit the address above.")
	}
}
