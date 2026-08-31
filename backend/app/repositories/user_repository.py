from sqlalchemy.orm import Session

from app.models.user import User


def get_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def list_all(
    db: Session, skip: int = 0, limit: int = 100, is_active: bool | None = None
) -> list[User]:
    query = db.query(User)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    return query.order_by(User.id.desc()).offset(skip).limit(limit).all()


def list_active(db: Session) -> list[User]:
    return db.query(User).filter(User.is_active.is_(True)).all()


def count(db: Session) -> int:
    return db.query(User).count()


def count_active_commanders(db: Session, exclude_id: int | None = None) -> int:
    """Dem tai khoan bac chi huy (commander HOAC admin) dang hoat dong."""
    query = db.query(User).filter(
        User.role.in_(("commander", "admin")), User.is_active.is_(True)
    )
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.count()


def get_first_system(db: Session) -> User | None:
    return db.query(User).filter(User.is_system.is_(True)).first()


def create(
    db: Session,
    *,
    username: str,
    hashed_password: str,
    full_name: str,
    role: str,
    unit_id: int | None = None,
    directive_channel_access: bool = False,
    command_channel_access: bool = False,
    must_change_password: bool = False,
) -> User:
    user = User(
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        unit_id=unit_id,
        directive_channel_access=directive_channel_access,
        command_channel_access=command_channel_access,
        must_change_password=must_change_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
