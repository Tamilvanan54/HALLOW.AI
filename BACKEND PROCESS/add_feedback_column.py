from sqlalchemy import text

from database.connection import engine


try:

    with engine.connect() as conn:


        conn.execute(
            text(
                """
                ALTER TABLE feedback
                ADD COLUMN IF NOT EXISTS modified_answer TEXT;
                """
            )
        )


        conn.commit()


    print(
        "modified_answer column added successfully"
    )


except Exception as e:


    print(
        "Database Update Error:",
        e
    )