# Save graph visualization to file
def save_graph_visualization(graph, filename):
    try:
        graph_png = graph.get_graph().draw_mermaid_png()
        with open(filename, "wb") as f:
            f.write(graph_png)
        print(f"Graph visualization saved to '{filename}'")
    except Exception as e:
        print("Could not generate graph visualization:", e)
