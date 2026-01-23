# HPC Instructions (Bocconi)

## Connection

**SSH Alias:** `ssh bocconi-hpc` (configured in `~/.ssh/config`)
- Host: `lnode01-da.hpc.unibocconi.it`
- User: `gauthier`

## Job Scheduler: SLURM

### Key Partitions

| Partition | Time Limit | Nodes | Hardware | Use Case |
|-----------|------------|-------|----------|----------|
| `defq` (default) | 3 days | cnode01-08 | CPU only | General CPU jobs |
| `compute` | 15 days | cnode01-08 | CPU only | Long CPU jobs |
| `medium_gpu` | 3h 10m | gnode01, gnode03 | 4x A100 80GB | Quick GPU jobs |
| `gpu` | 1 day | gnode01, gnode03 | 4x A100 80GB | Standard GPU jobs |
| `long_gpu` | 3 days | gnode01, gnode03 | 4x A100 80GB | Long GPU jobs |
| `medium_gpunew` | 3h 10m | gnode05-08 | 2x H100 94GB | Quick GPU jobs (H100) |
| `gpunew` | 1 day | gnode05-08 | 2x H100 94GB | Standard GPU jobs (H100) |
| `long_gpunew` | 3 days | gnode05-08 | 2x H100 94GB | Long GPU jobs (H100) |
| `debug_cpu` / `debug_gpu` | 15 min | various | — | Quick tests |

### GPU Partition Selection

**For jobs ≤3h:** Use `medium_gpu` or `medium_gpunew` (often less congested)
**For jobs ≤1 day:** Use `gpu` or `gpunew`
**For jobs >1 day:** Use `long_gpu` or `long_gpunew`

A100 vs H100: Both are powerful. A100 nodes have 4 GPUs each, H100 nodes have 2. Check availability and pick whichever is free.

**Always check availability before submitting:**
```bash
ssh bocconi-hpc "sinfo -p gpu,gpunew,medium_gpu,medium_gpunew --format='%P %l %a %D %t %C'"
```

### Available Software

CUDA 12.1-12.8, MATLAB, Miniconda, OpenMPI, Stata

### Common Commands

```bash
ssh bocconi-hpc "squeue -u gauthier"      # Check job queue
ssh bocconi-hpc "sinfo -s"                 # Partition status
ssh bocconi-hpc "scancel <jobid>"          # Cancel job
ssh bocconi-hpc "sbatch script.sh"         # Submit job
ssh bocconi-hpc "module avail"             # List modules
```

## Workflows

### Job Management

1. **Check availability first**: `sinfo -p gpu,gpunew` before GPU jobs
2. Submit jobs with `sbatch` - always specify partition, time, and resources
3. Monitor running jobs with `squeue -u gauthier`
4. Fetch output files when complete
5. For GPU jobs, prefer `gpu` over `gpunew` unless H100s are needed
