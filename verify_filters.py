from fetcher import is_american_football

test_cases = [
    {
        "title": "Ravens pull plug on blockbuster Crosby trade after medical issues",
        "summary": "The Ravens have halted their blockbuster trade for Maxx Crosby due to medical concerns.",
        "url": "https://www.skysports.com/nfl/news/12040/13518050/maxx-crosby-baltimore-ravens-back-out-of-trade-for-las-vegas-raiders-defensive-end",
        "expected": True
    },
    {
        "title": "Bayer Leverkusen v Arsenal: Champions League live",
        "summary": "Champions League last 16, first leg live coverage.",
        "url": "https://www.theguardian.com/football/live/2026/mar/11/bayer-leverkusen-v-arsenal",
        "expected": True
    },
    {
        "title": "Super Bowl LVIII Highlights",
        "summary": "The Kansas City Chiefs take on the San Francisco 49ers.",
        "url": "https://www.skysports.com/nfl/news/12040/12345678/super-bowl-highlights",
        "expected": True
    },
    {
        "title": "Lionel Messi scores wonder goal",
        "summary": "Inter Miami star shines in MLS match.",
        "url": "https://www.bbc.com/sport/football/articles/c4geyndly41o",
        "expected": False
    },
    {
        "title": "NFL Draft Day 1 Recap",
        "summary": "Top prospects selected in the first round.",
        "url": "https://www.theguardian.com/sport/2026/mar/11/nfl-draft-recap",
        "expected": True
    },
    {
        "title": "Bayer Leverkusen v Arsenal: Champions League last 16, first leg\u2013 live",
        "summary": "Live coverage of the Champions League match.",
        "url": "https://www.theguardian.com/football/live/2026/mar/11/bayer-leverkusen-v-arsenal-champions-league-last-16-first-leg-live",
        "expected": True
    },
    {
        "title": "Premier League: Man City vs Liverpool - match report",
        "summary": "Manchester City and Liverpool play out a thrilling draw.",
        "url": "https://www.skysports.com/football/match-report/12040/12345/man-city-vs-liverpool",
        "expected": True
    }
]

def run_tests():
    from fetcher import is_american_football, is_live_report
    passed = 0
    for i, case in enumerate(test_cases):
        # Check both filters
        is_nfl = is_american_football(case["title"], case["summary"], case["url"])
        is_live = is_live_report(case["title"], case["summary"], case["url"])
        result = is_nfl or is_live
        
        if result == case["expected"]:
            print(f"Test case {i+1} PASSED")
            passed += 1
        else:
            print(f"Test case {i+1} FAILED: Expected {case['expected']}, got {result}")
            print(f"  Title: {case['title']}")
            print(f"  is_nfl: {is_nfl}, is_live: {is_live}")
    
    print(f"\nPassed {passed}/{len(test_cases)} tests.")

if __name__ == "__main__":
    run_tests()
