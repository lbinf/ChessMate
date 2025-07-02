from contextlib import contextmanager
from app.database import SessionLocal, DB_ENABLED
from app.models.chess_models import AiChess
from app.logging_config import logger
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert

@contextmanager
def get_db():
    if not DB_ENABLED:
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_analysis_to_db(db: Session, analysis_data: list):
    """
    Inserts or updates a list of analysis results in the ai_chess table.
    """
    if not db or not analysis_data:
        return

    dialect_name = db.bind.dialect.name
    if dialect_name == 'mysql':
        stmt = mysql_insert(AiChess).values(analysis_data)
        stmt = stmt.on_duplicate_key_update(
            chinese_move=stmt.inserted.chinese_move,
            source=stmt.inserted.source,
            score=stmt.inserted.score,
            rank=stmt.inserted.rank,
            note=stmt.inserted.note,
            win_rate=stmt.inserted.win_rate,
        )
    elif dialect_name == 'sqlite':
        stmt = sqlite_insert(AiChess).values(analysis_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['fen', 'is_move', 'move'],
            set_=dict(
                chinese_move=stmt.excluded.chinese_move,
                source=stmt.excluded.source,
                score=stmt.excluded.score,
                rank=stmt.excluded.rank,
                note=stmt.excluded.note,
                win_rate=stmt.excluded.win_rate,
            )
        )
    else:
        logger.warning(f"Upsert logic not implemented for dialect: {dialect_name}")
        return

    try:
        db.execute(stmt)
        db.commit()
    except Exception as e:
        logger.error(f"Error bulk inserting analysis: {e}")
        db.rollback()

    logger.info(f"Upserted {len(analysis_data)} analysis results to database.") 