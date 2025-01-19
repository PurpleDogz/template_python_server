# Test for time_util.py

import unittest
from datetime import datetime
from freezegun import freeze_time

from time_util import (
    DurationTimer,
    get_months_back,
    get_start_date,
    get_date_back,
    get_start_date_absolute,
    START_ALL,
    START_1MONTH,
    START_3MONTHS,
    START_6MONTHS,
    START_12MONTHS,
    START_24MONTHS,
    START_CURRENT_WEEK, 
    START_LAST_WEEK,
    get_period_format,
    PERIOD_DAY,
    PERIOD_WEEK,
    PERIOD_MONTH
)
    
class TestDurationTimer(unittest.TestCase):
    def test_format_time(self):
        # Test milliseconds
        assert DurationTimer.formatTime(500) == "500 millisecond(s)"
        assert DurationTimer.formatTime(999) == "999 millisecond(s)"
        
        # Test seconds
        assert DurationTimer.formatTime(1000) == "1 second(s)"
        assert DurationTimer.formatTime(45000) == "45 second(s)"
        assert DurationTimer.formatTime(59999) == "59 second(s)"
        
        # Test minutes only
        assert DurationTimer.formatTime(60000) == "1 minute(s)"
        assert DurationTimer.formatTime(120000) == "2 minute(s)"
        
        # Test minutes with seconds
        assert DurationTimer.formatTime(61000) == "1 minute(s) 1 second(s)"
        assert DurationTimer.formatTime(185000) == "3 minute(s) 5 second(s)"
        
        # Test edge cases
        assert DurationTimer.formatTime(0) == "0 millisecond(s)"
        assert DurationTimer.formatTime(3599999) == "59 minute(s) 59 second(s)"

class TestGetStartDate(unittest.TestCase):
    def setUp(self):
        # Setup test dates and timezones
        self.test_date = datetime(2024, 3, 15)  # A Friday
        self.timezone = 'UTC'  # Using string instead of pytz.UTC
        
    def test_get_start_date_none(self):
        result = get_start_date(self.timezone, START_ALL)
        self.assertIsNone(result)
        
    def test_get_start_date_empty(self):
        result = get_start_date(self.timezone, "")
        self.assertIsNone(result)
        
    def test_get_start_date_current_week(self):
        result = get_start_date(
            self.timezone,
            START_CURRENT_WEEK,
            base_date=self.test_date
        )
        expected = datetime(2024, 3, 11)  # Monday of test week
        self.assertEqual(result.date(), expected.date())
        
    def test_get_start_date_last_week(self):
        result = get_start_date(
            self.timezone,
            START_LAST_WEEK,
            base_date=self.test_date
        )
        expected = datetime(2024, 3, 4)  # Monday of previous week
        self.assertEqual(result.date(), expected.date())
        
    def test_get_start_date_round_to_month(self):
        result = get_start_date(
            self.timezone,
            START_CURRENT_WEEK,
            round_to_month=True,
            base_date=self.test_date
        )
        expected = datetime(2024, 3, 1)  # First of the month
        self.assertEqual(result.date(), expected.date())

class TestGetMonthsBack(unittest.TestCase):
    def test_get_months_back_all(self):
        result = get_months_back(START_ALL)
        self.assertIsNone(result)
    
    def test_get_months_back_1month(self):
        result = get_months_back(START_1MONTH)
        self.assertEqual(result, 1)
    
    def test_get_months_back_3months(self):
        result = get_months_back(START_3MONTHS)
        self.assertEqual(result, 3)
    
    def test_get_months_back_6months(self):
        result = get_months_back(START_6MONTHS)
        self.assertEqual(result, 6)
    
    def test_get_months_back_12months(self):
        result = get_months_back(START_12MONTHS)
        self.assertEqual(result, 12)
    
    def test_get_months_back_24months(self):
        result = get_months_back(START_24MONTHS)
        self.assertEqual(result, 24)
    
    def test_get_months_back_invalid(self):
        result = get_months_back("INVALID_START")
        self.assertIsNone(result)
    
    def test_get_months_back_none(self):
        result = get_months_back(None)
        self.assertIsNone(result)

class TestGetDateBack(unittest.TestCase):
    def setUp(self):
        self.timezone = 'UTC'
        self.frozen_time = "2024-03-15 10:00:00"
    
    @freeze_time("2024-03-15 10:00:00")
    def test_days_only(self):
        """Test with days parameter only"""
        result = get_date_back(self.timezone, 5)
        expected = datetime(2024, 3, 10, 23, 59, 59)
        self.assertEqual(result.replace(tzinfo=None), expected)

    @freeze_time("2024-03-15 10:00:00")
    def test_zero_days(self):
        """Test with zero days"""
        result = get_date_back(self.timezone, 0)
        expected = datetime(2024, 3, 15, 23, 59, 59)
        self.assertEqual(result.replace(tzinfo=None), expected)

    @freeze_time("2024-03-15 10:00:00")
    def test_negative_days(self):
        """Test with negative days"""
        result = get_date_back(self.timezone, -5)
        expected = datetime(2024, 3, 20, 23, 59, 59)
        self.assertEqual(result.replace(tzinfo=None), expected)

    @freeze_time("2024-03-15 10:00:00")
    def test_different_timezone(self):
        """Test with non-UTC timezone"""
        est_timezone = 'America/New_York'
        result = get_date_back(est_timezone, 1)
        self.assertEqual(result.strftime('%Y-%m-%d %H'), "2024-03-14 23")

class TestGetPeriodFormat(unittest.TestCase):

    def test_period_day(self):
        """Test daily period format"""
        result = get_period_format(PERIOD_DAY)
        self.assertEqual(result, "%Y-%m-%d")

    def test_period_week(self):
        """Test weekly period format"""
        result = get_period_format(PERIOD_WEEK)
        self.assertEqual(result, "%Y-%m")

    def test_period_month(self):
        """Test monthly period format"""
        result = get_period_format(PERIOD_MONTH)
        self.assertEqual(result, "%Y-%m")

    def test_invalid_period(self):
        """Test invalid period"""
        result = get_period_format("INVALID_PERIOD")
        self.assertEqual(result, "%Y-%m")

    def test_none_period(self):
        """Test None period"""
        result = get_period_format(None)
        self.assertEqual(result, "%Y-%m")

    def test_empty_period(self):
        """Test empty string period"""
        result = get_period_format("")
        self.assertEqual(result, "%Y-%m")
                    
if __name__ == "__main__":
    unittest.main()
    #test_util_1(True, True)
    # test_plan_1(False, False)
