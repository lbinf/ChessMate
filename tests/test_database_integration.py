import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.services.analysis import analyze_fen
from app.services.db_service import get_db, add_analysis_to_db
from app.models.chess_models import AiChess
from app.database import Base, engine, DB_ENABLED

class TestDatabaseIntegration(unittest.TestCase):

    def setUp(self):
        """Set up a test database and session."""
        if not DB_ENABLED:
            self.skipTest("Database is not enabled, skipping integration tests.")
        
        # Use an in-memory SQLite database for testing
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def tearDown(self):
        """Tear down the test database."""
        Base.metadata.drop_all(self.engine)

    @patch('app.services.analysis.get_db')
    @patch('app.services.analysis.engine_instance')
    @patch('app.services.analysis.get_chessdb_analysis')
    def test_analyze_fen_and_save_to_db(self, mock_get_chessdb_analysis, mock_engine_instance, mock_get_db):
        """
        Test that analyze_fen correctly processes a FEN, calls external services,
        and saves results to the database.
        """
        # --- Mocking Setup ---
        mock_db_session = self.Session()
        mock_get_db.return_value = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db_session

        # Mock chessdb.cn response
        mock_get_chessdb_analysis.return_value = []

        # Mock local engine response
        mock_engine_instance.get_best_move.return_value = ('h2e2', ['info depth 1 score cp 5'], 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w')
        mock_engine_instance.get_last_analysis_lines.return_value = ['info depth 1 score cp 5', 'bestmove h2e2']
        
        # --- Test Execution ---
        fen = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w'
        board_array = [['r','n','b','a','k','a','b','n','r'], ['','','','','','','','',''], ['','c','','','','','','c',''],['p','','p','','p','','p','','p'],[],[],['P','','P','','P','','P','','P'],['','C','','','','','','C',''],['','','','','','','','',''],['R','N','B','A','K','A','B','N','R']]

        analyze_fen(fen, is_red=True, board_array=board_array)

        # --- Debug: Check all records in database ---
        all_records = mock_db_session.query(AiChess).all()
        print(f"DEBUG: All records in database: {len(all_records)}")
        for record in all_records:
            print(f"DEBUG: Record - fen: '{record.fen}', move: '{record.move}', source: {record.source}, is_move: '{record.is_move}'")
        
        query_fen = fen.split()[0]
        print(f"DEBUG: Querying with fen='{query_fen}', move='h2e2', source=0")

        # --- Assertions ---
        # 1. Verify local AI analysis was saved (since cloud_moves is empty)
        result = mock_db_session.query(AiChess).filter_by(fen=fen.split()[0], move='h2e2', source=0).first()
        self.assertIsNotNone(result)
        self.assertEqual(result.move, 'h2e2')
        self.assertEqual(result.score, 5)  # 这里假设 mock_engine_instance 返回的 score 也是 5

        # 2. Verify services were called
        mock_get_chessdb_analysis.assert_called_once_with(fen)
        mock_engine_instance.get_best_move.assert_called_once_with(fen, 'w')

    def test_insert_and_query_analysis(self):
        with get_db() as db:
            # Insert a test record
            data = [{
                'fen': 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C1C5/9/RNBAKABNR',
                'is_move': 'w',
                'move': 'b2e2',
                'source': 0,
                'score': 123,
                'rank': 1,
                'note': 'test',
                'win_rate': 5050,
                'chinese_move': '测试'
            }]
            add_analysis_to_db(db, data)
            # Query and assert
            result = db.query(AiChess).filter_by(fen='rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C1C5/9/RNBAKABNR', move='b2e2').first()
            self.assertIsNotNone(result)
            self.assertEqual(result.score, 123)
            self.assertEqual(result.win_rate, 5050)

if __name__ == '__main__':
    unittest.main() 