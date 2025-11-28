import matplotlib.pyplot as plt
import networkx as nx

# 1. Define the Data
# Nodes: (ID, Label, Group, Size)
# Groups: 1=Axis(China/Russia), 2=Middle/Shifting(India/Turkey), 3=West(USA/Ukraine)
nodes = [
    ("China", "Xi Jinping\n(CHINA)", 1, 3000),
    ("Russia", "Vladimir Putin\n(RUSSIA)", 1, 2800),
    ("India", "Narendra Modi\n(INDIA)", 2, 2500),
    ("Turkey", "R.T. Erdoğan\n(TURKEY)", 2, 1800),
    ("Belarus", "A. Lukashenko\n(BELARUS)", 1, 1200),
    ("NK", "Kim Jong-un\n(N. KOREA)", 1, 1200),
    ("USA", "Donald Trump\n(USA)", 3, 2500),
    ("Ukraine", "UKRAINE", 3, 1500),
]

# Edges: (Source, Target, Type, Label)
# Type: 'friendly' or 'hostile'
edges = [
    ("China", "Russia", "friendly", "Limitless\nPartnership"),
    ("China", "India", "friendly", "Rebuilding\nTies"),
    ("China", "Turkey", "friendly", "Counter\nTerrorism"),
    ("Russia", "Belarus", "friendly", "Key Ally"),
    ("Russia", "NK", "friendly", "Parade\nGuest"),
    ("China", "USA", "hostile", "Common\nFoe"),
    ("Russia", "USA", "hostile", "Mutual\nOpponent"),
    ("USA", "India", "hostile", "50% Tariffs\n(Punitive)"),
    ("Russia", "Ukraine", "hostile", "Invasion"),
    ("Ukraine", "China", "hostile", "Accused of\nAiding RF"),
]

# 2. Initialize Graph
G = nx.DiGraph()

for n, label, group, size in nodes:
    G.add_node(n, label=label, group=group, size=size)

for u, v, type_, label in edges:
    G.add_edge(u, v, type=type_, label=label)

# 3. Layout Settings
# We want China/Russia central, USA distinct, India bridging.
pos = {
    "China": (0, 0),
    "Russia": (0.5, 0.5),
    "India": (-0.4, -0.6),
    "Turkey": (0.4, -0.4),
    "Belarus": (0.9, 0.7),
    "NK": (0.7, 0.3),
    "USA": (-0.8, 0.5),
    "Ukraine": (-0.3, 0.8),
}

# 4. Drawing Configuration
plt.figure(figsize=(14, 10))
ax = plt.gca()

# Define Colors
group_colors = {1: '#A8D5BA', 2: '#FCEEB5', 3: '#F49AC2'} # Greenish, Yellowish, Reddish
edge_colors = {'friendly': '#2E8B57', 'hostile': '#B22222'} # SeaGreen, Firebrick

# Draw Nodes
for n, label, group, size in nodes:
    nx.draw_networkx_nodes(G, pos, nodelist=[n], node_color=group_colors[group], 
                           node_size=size, alpha=0.9, edgecolors='gray')
    nx.draw_networkx_labels(G, pos, labels={n: label}, font_size=9, font_weight='bold')

# Draw Edges
friendly_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'friendly']
hostile_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'hostile']

nx.draw_networkx_edges(G, pos, edgelist=friendly_edges, edge_color=edge_colors['friendly'], 
                       width=2, arrowstyle='-|>', arrowsize=20, connectionstyle="arc3,rad=0.1")
nx.draw_networkx_edges(G, pos, edgelist=hostile_edges, edge_color=edge_colors['hostile'], 
                       width=2, arrowstyle='-|>', arrowsize=20, style='dashed', connectionstyle="arc3,rad=0.1")

# Draw Edge Labels
edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, font_color='black', label_pos=0.5)

# 5. Legend and Titles
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#A8D5BA', label='SCO / Anti-West Bloc', markersize=15),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#FCEEB5', label='Shifting / Balancing', markersize=15),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#F49AC2', label='Western / Opposing', markersize=15),
    Line2D([0], [0], color='#2E8B57', lw=2, label='Alliance / Cooperation'),
    Line2D([0], [0], color='#B22222', lw=2, linestyle='--', label='Conflict / Pressure'),
]
ax.legend(handles=legend_elements, loc='upper left', title="Entity Relationships")

plt.title("Geopolitical Dynamics at the SCO Summit in Tianjin", fontsize=16, fontweight='bold')
plt.axis('off')
plt.tight_layout()
plt.show()