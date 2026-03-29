from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./quickapply.db")

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


def _sqlite_fk_exists(conn, table_name: str, target_table: str = "users") -> bool:
    rows = conn.exec_driver_sql(f"PRAGMA foreign_key_list({table_name})").fetchall()
    return any(row[2] == target_table for row in rows)


def _migrate_sqlite_fk_tables(conn):
    conn.exec_driver_sql("PRAGMA foreign_keys=OFF")

    if not _sqlite_fk_exists(conn, "profiles"):
        conn.exec_driver_sql(
            """
            CREATE TABLE profiles_new (
                id VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                full_name VARCHAR,
                email VARCHAR,
                phone VARCHAR,
                nationality VARCHAR,
                location VARCHAR,
                degree VARCHAR,
                field_of_study VARCHAR,
                university VARCHAR,
                gpa VARCHAR,
                graduation_year VARCHAR,
                work_experience JSON,
                skills JSON,
                languages JSON,
                certifications JSON,
                target_countries JSON,
                target_programs JSON,
                application_types JSON,
                cv_raw_text TEXT,
                ai_summary TEXT,
                ai_strengths JSON,
                ai_gaps JSON,
                updated_at DATETIME,
                created_at DATETIME,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )
        conn.exec_driver_sql(
            """
            INSERT INTO profiles_new (
                id, user_id, full_name, email, phone, nationality, location,
                degree, field_of_study, university, gpa, graduation_year,
                work_experience, skills, languages, certifications,
                target_countries, target_programs, application_types,
                cv_raw_text, ai_summary, ai_strengths, ai_gaps,
                updated_at, created_at
            )
            SELECT
                p.id, p.user_id, p.full_name, p.email, p.phone, p.nationality, p.location,
                p.degree, p.field_of_study, p.university, p.gpa, p.graduation_year,
                p.work_experience, p.skills, p.languages, p.certifications,
                p.target_countries, p.target_programs, p.application_types,
                p.cv_raw_text, p.ai_summary, p.ai_strengths, p.ai_gaps,
                p.updated_at, p.created_at
            FROM profiles p
            JOIN users u ON u.id = p.user_id
            """
        )
        conn.exec_driver_sql("DROP TABLE profiles")
        conn.exec_driver_sql("ALTER TABLE profiles_new RENAME TO profiles")
        conn.exec_driver_sql("CREATE INDEX ix_profiles_user_id ON profiles (user_id)")

    if not _sqlite_fk_exists(conn, "applications"):
        conn.exec_driver_sql(
            """
            CREATE TABLE applications_new (
                id VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                type VARCHAR NOT NULL,
                position_title VARCHAR,
                organization VARCHAR,
                location VARCHAR,
                job_ad_text TEXT,
                status VARCHAR,
                deadline DATETIME,
                applied_date DATETIME,
                contact_email VARCHAR,
                contact_name VARCHAR,
                generated_cv TEXT,
                generated_cover_letter TEXT,
                generated_sop TEXT,
                notes TEXT,
                reminders JSON,
                created_at DATETIME,
                updated_at DATETIME,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """
        )
        conn.exec_driver_sql(
            """
            INSERT INTO applications_new (
                id, user_id, type, position_title, organization, location,
                job_ad_text, status, deadline, applied_date,
                contact_email, contact_name,
                generated_cv, generated_cover_letter, generated_sop,
                notes, reminders, created_at, updated_at
            )
            SELECT
                a.id, a.user_id, a.type, a.position_title, a.organization, a.location,
                a.job_ad_text, a.status, a.deadline, a.applied_date,
                a.contact_email, a.contact_name,
                a.generated_cv, a.generated_cover_letter, a.generated_sop,
                a.notes, a.reminders, a.created_at, a.updated_at
            FROM applications a
            JOIN users u ON u.id = a.user_id
            """
        )
        conn.exec_driver_sql("DROP TABLE applications")
        conn.exec_driver_sql("ALTER TABLE applications_new RENAME TO applications")
        conn.exec_driver_sql("CREATE INDEX ix_applications_user_id ON applications (user_id)")

    conn.exec_driver_sql("PRAGMA foreign_keys=ON")


async def init_db():
    from models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        if engine.dialect.name == "sqlite":
            await conn.run_sync(_migrate_sqlite_fk_tables)
