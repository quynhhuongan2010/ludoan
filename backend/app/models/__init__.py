"""Goi `app.models` - import tat ca model de dang ky mapper voi SQLAlchemy.

`import app.models` (hoac `from app.models import ...`) se nap toan bo lop model,
bao dam moi `relationship(...)` giua cac bang deu phan giai duoc ten lop khi
`Base.metadata.create_all` / configure mappers chay. Cac script kiem thu chi can
`import app.models` thay vi liet ke tay tung module (tranh loi "failed to locate
a name" khi mot ben cua quan he chua duoc import).
"""

from app.models import (  # noqa: F401
    announcement,
    audit_log,
    chat,
    command_thread,
    contact,
    directive,
    directive_assignment,
    directive_thread,
    document,
    duty_plan_attachment,
    duty_schedule,
    duty_shift_handover,
    duty_week_plan,
    education_material,
    item,
    leadership_task,
    official_dispatch,
    post,
    unit,
    user,
)
