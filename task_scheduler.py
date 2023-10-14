import datetime
import win32com.client
import win32security
import win32api
import win32con
import pywintypes

desc = win32security.GetFileSecurity(
    ".", win32security.OWNER_SECURITY_INFORMATION
)
sid = desc.GetSecurityDescriptorOwner()
sidstr = win32security.ConvertSidToStringSid(sid)
username = win32api.GetUserNameEx(win32con.NameSamCompatible)

TRIGGER_TYPE_DAILY = 2
ACTION_TYPE_EXEC = 0
TASK_INSTANCES_IGNORE_NEW = 2
TASK_CREATE_OR_UPDATE = 0x6
TASK_LOGON_NONE = 0
TASK_LOGON_INTERACTIVE_TOKEN = 3
TASK_RUNLEVEL_LUA = 0

scheduler = win32com.client.Dispatch('Schedule.Service')
scheduler.Connect()
root = scheduler.GetFolder('\\')

try:
    folder = root.GetFolder('Automatic Darkmode')
except pywintypes.com_error:
    folder = root.CreateFolder('Automatic Darkmode')


def create_or_update_task(
    name: str,
    description: str,
    time: datetime.time,
    actions: list[tuple[str, str]]
):
    task_def = scheduler.NewTask(0)

    # Create the trigger
    trigger = task_def.Triggers.Create(TRIGGER_TYPE_DAILY)
    time_now = datetime.datetime.now()
    time_start = datetime.datetime(time_now.year, time_now.month, time_now.day, time.hour, time.minute, time.second)
    trigger.StartBoundary = time_start.isoformat()

    # Create actions
    if len(actions) > 0:
        for action in actions:
            new_action = task_def.Actions.Create(ACTION_TYPE_EXEC)
            new_action.Path = action[0]
            new_action.Arguments = action[1]
    task_def.Actions.Context = 'Author'
    
    task_def.Settings.AllowDemandStart = True
    task_def.Settings.DisallowStartIfOnBatteries = False
    task_def.Settings.Enabled = True
    task_def.Settings.RestartCount = 3
    task_def.Settings.StopIfGoingOnBatteries = False
    task_def.Settings.WakeToRun = False
    task_def.Settings.StartWhenAvailable = True
    task_def.Settings.MultipleInstances = TASK_INSTANCES_IGNORE_NEW

    task_def.Principal.LogonType = TASK_LOGON_INTERACTIVE_TOKEN
    task_def.Principal.RunLevel = TASK_RUNLEVEL_LUA
    task_def.Principal.UserID = sidstr
    task_def.Principal.Id = 'Author'

    # Registration info 
    task_def.RegistrationInfo.Description = description
    task_def.RegistrationInfo.Author = username

    folder.RegisterTaskDefinition(name, task_def, TASK_CREATE_OR_UPDATE, '', '', TASK_LOGON_INTERACTIVE_TOKEN)


def delete_task(name: str):
    folder.DeleteTask(name)
