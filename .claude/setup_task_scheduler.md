# Setting Up Windows Task Scheduler for SF6 Data Export

## Steps to Schedule Monthly Export (2nd Friday)

### 1. Open Task Scheduler
- Press `Win + R`, type `taskschd.msc`, press Enter
- Or search "Task Scheduler" in Start menu

### 2. Create Basic Task
1. Click "Create Basic Task..." in right panel
2. **Name**: "SF6 Monthly Data Export"
3. **Description**: "Automated export of SF6 battle diagrams and usage stats on 2nd Friday of each month"

### 3. Configure Trigger
1. **When**: Select "Monthly"
2. **Months**: Select all 12 months
3. **On**: Select "Second" and "Friday"
4. **Start**: Set desired time (e.g., 2:00 AM for minimal site traffic)

### 4. Configure Action
1. **Action**: Select "Start a program"
2. **Program/script**: Browse to `run_monthly_export.bat`
3. **Start in**: `D:\Files from old PC - Documents\Coding Projects\SF6_Analysis\sf6AnalysisData`

### 5. Advanced Settings
1. **Run whether user is logged on or not**: Check this
2. **Run with highest privileges**: Check this
3. **Configure for**: Windows 10/11

### 6. Test the Task
- Right-click the created task → "Run"
- Verify it executes successfully

## Important Notes

- **Firefox Requirement**: Firefox must be installed on the system
- **Python Environment**: Ensure Python and all dependencies are available system-wide
- **Network Access**: System must have internet access
- **User Permissions**: Task should run with appropriate permissions for file writing

## Troubleshooting

If the task fails:
1. Check the task history for error details
2. Verify paths in the batch file are correct
3. Test running the batch file manually first
4. Ensure all Python dependencies are installed globally