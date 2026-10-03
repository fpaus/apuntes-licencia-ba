// Command licencia serves the study app from files embedded in the binary and opens the browser.
package main

import (
	"embed"
	"errors"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os/exec"
	"runtime"
	"syscall"
)

//go:embed app content
var files embed.FS

// Fixed port: the browser keys saved progress (localStorage) by origin, port included.
const defaultAddr = "127.0.0.1:8642"

func main() {
	noOpen := flag.Bool("no-open", false, "do not open the browser")
	addr := flag.String("addr", defaultAddr, "listen address; 0.0.0.0:8642 serves the local network")
	flag.Parse()
	url := "http://" + *addr + "/app/"
	ln, err := net.Listen("tcp", *addr)
	// ponytail: Windows reports WSAEADDRINUSE, not EADDRINUSE; any listen error there is taken as "already running".
	if errors.Is(err, syscall.EADDRINUSE) || (err != nil && runtime.GOOS == "windows") {
		fmt.Println("La app ya está abierta en", url)
		openBrowser(url)
		return
	}
	if err != nil {
		panic(err)
	}
	http.Handle("/", http.RedirectHandler("/app/", http.StatusFound))
	// Embedded files carry no modification time; no-cache keeps a rebuilt binary from serving stale content.
	static := http.FileServer(http.FS(files))
	noCache := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-cache")
		static.ServeHTTP(w, r)
	})
	http.Handle("/app/", noCache)
	http.Handle("/content/", noCache)
	fmt.Println("Licencia de conducir — app de estudio")
	fmt.Println("Abrí", url, "en el navegador. Cerrá esta ventana para salir.")
	if !*noOpen {
		openBrowser(url)
	}
	panic(http.Serve(ln, nil))
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	_ = cmd.Start() // the URL is printed anyway
}
