# Coding Conventions

## Figures

### General Style
- **No figure titles**: Titles will be added in Overleaf/LaTeX, not in Python
- **Font sizes**: Use larger fonts for publication quality
  - Axis labels: `fontsize=16` or `fontsize=18`, `fontweight="bold"`
  - Tick labels: `labelsize=12` or `labelsize=14`
  - Legends: `fontsize=14` or `fontsize=16`
- **Spines**: Remove top and right spines for cleaner look
  ```python
  ax.spines["top"].set_visible(False)
  ax.spines["right"].set_visible(False)
  ```

### Confidence Intervals
- Alpha around 0.3 for visibility: `alpha=0.3`

### Party Colors (US Politics)
- Democrats: `"blue"` or `"tab:blue"`
- Republicans: `"red"` or `"tab:red"`

### Output Formats
- Save both PNG (for preview) and PDF (for LaTeX)
- Use `dpi=300` for PNG files
- Use `bbox_inches="tight"` when saving

### Example Template
```python
fig, ax = plt.subplots(figsize=(10, 6))

# Plot data...

ax.set_xlabel("X Label", fontsize=18, fontweight="bold")
ax.set_ylabel("Y Label", fontsize=18, fontweight="bold")
ax.tick_params(labelsize=14)
ax.legend(fontsize=16)
ax.grid(True, alpha=0.3)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()
plt.savefig(path, dpi=300, bbox_inches="tight")
plt.savefig(path.replace(".png", ".pdf"), bbox_inches="tight")
```
