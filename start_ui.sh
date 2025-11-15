#!/bin/bash

# Start the Web UI

echo "=================================================="
echo "  Starting Web UI"
echo "=================================================="
echo ""
echo "Web UI will be available at: http://localhost:8080"
echo ""
echo "Make sure the API server is running on http://localhost:5000"
echo "If not, run './start_server.sh' in another terminal"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=================================================="
echo ""

cd frontend
python3 -m http.server 8080
