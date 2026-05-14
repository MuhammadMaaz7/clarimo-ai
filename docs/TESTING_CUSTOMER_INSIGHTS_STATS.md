# Testing Guide: Customer Insights Dashboard Stats

## Overview
This guide provides step-by-step instructions to test the Customer Insights stats integration in the dashboard and profile pages.

## Prerequisites
- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:5173` (or configured port)
- Valid user account with authentication token
- MongoDB database accessible

## Test Scenarios

### Scenario 1: Fresh User (No Analyses)

#### Steps:
1. Log in with a new user account
2. Navigate to Dashboard (`/dashboard`)

#### Expected Results:
- ✅ Customer Insights card shows `0` analyses
- ✅ Segments and communities show `0`
- ✅ No Customer Insights in recent activity
- ✅ Control Center shows `0` for Customer Insights
- ✅ Total actions count is correct (sum of all modules)

#### Verification:
```
Dashboard Stats Card:
- Total: 0
- Segments: 0
- Communities: 0

Control Center:
- Customer Insights: 0

Profile Page Quick Actions:
- Customer Insights: 0
```

---

### Scenario 2: Create First Analysis

#### Steps:
1. Navigate to Customer Insights (`/customer-insights`)
2. Enter a valid business idea (e.g., "AI-powered fitness app for busy professionals")
3. Optionally add target market
4. Click "Start Analysis"
5. Wait for analysis to complete (status: "completed")
6. Navigate back to Dashboard

#### Expected Results:
- ✅ Customer Insights card shows `1` analysis
- ✅ Segments count shows actual number (e.g., 3 segments)
- ✅ Communities count shows actual number (e.g., 5 communities)
- ✅ Customer Insights appears in recent activity
- ✅ Control Center shows `1` for Customer Insights
- ✅ Total actions count increased by 1

#### Verification:
```
Dashboard Stats Card:
- Total: 1
- Segments: [actual count from analysis]
- Communities: [actual count from analysis]

Recent Activity:
- "Customer Insights Analysis" with pink icon
- Shows "Processed 1 Entity"
- Shows creation date

Control Center:
- Customer Insights: 1

Profile Page Quick Actions:
- Customer Insights: 1
```

---

### Scenario 3: Multiple Analyses

#### Steps:
1. Create 3 different Customer Insights analyses:
   - Analysis 1: "SaaS tool for remote teams"
   - Analysis 2: "E-commerce platform for handmade goods"
   - Analysis 3: "Mobile app for language learning"
2. Wait for all analyses to complete
3. Navigate to Dashboard

#### Expected Results:
- ✅ Customer Insights card shows `3` analyses
- ✅ Segments count is sum of all analyses (e.g., 3+4+2 = 9)
- ✅ Communities count is sum of all analyses (e.g., 5+6+4 = 15)
- ✅ Recent activity shows latest Customer Insights analysis
- ✅ Control Center shows `3` for Customer Insights
- ✅ Total actions count includes all 3 analyses

#### Verification:
```
Dashboard Stats Card:
- Total: 3
- Segments: [sum of all segments]
- Communities: [sum of all communities]

Recent Activity:
- Shows most recent Customer Insights analysis
- Click navigates to /customer-insights/history

Control Center:
- Customer Insights: 3
- Click navigates to /customer-insights/history

Profile Page Quick Actions:
- Customer Insights: 3
```

---

### Scenario 4: Mixed Module Activities

#### Steps:
1. Create analyses in multiple modules:
   - 2 Problem Discovery analyses
   - 1 Idea Validation
   - 2 Competitor Analyses
   - 3 Customer Insights analyses
   - 1 Launch Plan
   - 1 GTM Strategy
2. Navigate to Dashboard

#### Expected Results:
- ✅ All module cards show correct counts
- ✅ Customer Insights shows `3` with correct segments/communities
- ✅ Recent activity shows latest 3 activities (may include Customer Insights)
- ✅ Total actions = 2+1+2+3+1+1 = 10

#### Verification:
```
Dashboard Stats:
- Problem Discovery: 2
- Ideas: 1
- Competitor Analysis: 2
- Customer Insights: 3 (with segments and communities)
- Launch Planning: 1
- GTM Strategy: 1

Total Actions: 10

Recent Activity:
- Shows 3 most recent activities
- Sorted by date (newest first)
- May include Customer Insights if recent
```

---

### Scenario 5: Navigation Tests

#### Steps:
1. From Dashboard, click on Customer Insights card
2. Verify navigation to `/customer-insights/history`
3. Return to Dashboard
4. Click "Go" button on Customer Insights card
5. Verify navigation to `/customer-insights`
6. Return to Dashboard
7. Click on Customer Insights in Control Center
8. Verify navigation to `/customer-insights/history`
9. Navigate to Profile page
10. Click on Customer Insights in Quick Actions
11. Verify navigation to `/customer-insights/history`

#### Expected Results:
- ✅ All navigation links work correctly
- ✅ History page shows all analyses
- ✅ Each analysis shows segments_found and communities_found
- ✅ New analysis page loads correctly

---

### Scenario 6: Real-time Updates

#### Steps:
1. Open Dashboard in browser
2. Create a new Customer Insights analysis
3. Wait for completion
4. Refresh Dashboard (or wait for auto-refresh if implemented)

#### Expected Results:
- ✅ Stats update to show new analysis
- ✅ Segments and communities counts update
- ✅ Recent activity includes new analysis
- ✅ Total actions count increases

---

### Scenario 7: Error Handling

#### Steps:
1. Stop backend server
2. Navigate to Dashboard
3. Observe loading state and error handling
4. Restart backend server
5. Refresh Dashboard

#### Expected Results:
- ✅ Loading spinner shows while fetching
- ✅ Graceful error handling if backend unavailable
- ✅ Stats load correctly after backend restart
- ✅ No console errors related to Customer Insights

---

## API Testing

### Test Backend Endpoint Directly

```bash
# Get Customer Insights history
curl -X GET "http://localhost:8000/api/customer-insights/history" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Expected Response:
[
  {
    "analysis_id": "uuid-here",
    "startup_idea": "Your business idea",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00",
    "completed_at": "2024-01-01T00:05:00",
    "segments_found": 3,
    "communities_found": 5
  }
]
```

---

## Browser Console Testing

### Check Stats Object

Open browser console and run:

```javascript
// Check if stats are loaded
console.log('Dashboard Stats:', window.__dashboardStats);

// Should show:
{
  customerInsights: {
    total: 3,
    totalSegments: 9,
    totalCommunities: 15,
    latest: "2024-01-01T00:00:00",
    latestTitle: "Your business idea"
  }
}
```

---

## Visual Verification Checklist

### Dashboard Page
- [ ] Customer Insights card has pink theme (pink-500)
- [ ] Card shows total analyses count
- [ ] Card shows segments and communities count
- [ ] Card has "History" and "Go" buttons
- [ ] Buttons navigate correctly
- [ ] Card has hover effects
- [ ] Grid layout shows 6 cards properly (not cramped)

### Recent Activity
- [ ] Customer Insights shows with pink icon (Users icon)
- [ ] Activity text: "Customer Insights Analysis"
- [ ] Shows correct count and date
- [ ] Click navigates to history page
- [ ] Hover effects work

### Control Center
- [ ] Customer Insights shows correct count
- [ ] Click navigates to history page
- [ ] Hover effects work

### Profile Page
- [ ] Quick Actions shows Customer Insights
- [ ] Count is correct
- [ ] Click navigates to history page
- [ ] Icon and styling match other actions

---

## Performance Testing

### Load Time
- [ ] Dashboard loads within 2 seconds
- [ ] Stats fetch completes within 1 second
- [ ] No unnecessary re-renders
- [ ] No memory leaks

### Network Requests
- [ ] Only one request to `/customer-insights/history`
- [ ] Request uses proper authentication
- [ ] Response is cached appropriately
- [ ] Failed requests handled gracefully

---

## Regression Testing

### Other Modules Still Work
- [ ] Problem Discovery stats display correctly
- [ ] Ideas stats display correctly
- [ ] Competitor Analysis stats display correctly
- [ ] Launch Planning stats display correctly
- [ ] GTM Strategy stats display correctly
- [ ] Total actions count is accurate

---

## Edge Cases

### Test Case 1: Analysis in Progress
- Create analysis but don't wait for completion
- Dashboard should show analysis with status "processing"
- Segments and communities may be 0 until completion

### Test Case 2: Failed Analysis
- Create analysis that fails (invalid input)
- Dashboard should still count the analysis
- Status should show "failed"

### Test Case 3: Very Large Numbers
- Create 100+ analyses (if possible)
- Verify counts display correctly
- Verify no UI overflow issues

### Test Case 4: Empty Startup Idea
- Analysis with very short or empty idea
- Verify latestTitle handles gracefully

---

## Automated Testing (Optional)

### Unit Tests
```typescript
describe('useDashboardStats', () => {
  it('should fetch Customer Insights stats', async () => {
    // Mock customerInsightsApi.getHistory()
    // Verify stats.customerInsights is populated
  });

  it('should calculate total segments correctly', async () => {
    // Mock multiple analyses with different segment counts
    // Verify totalSegments is sum of all
  });

  it('should include Customer Insights in totalActions', async () => {
    // Verify totalActions includes customerInsights.total
  });
});
```

### Integration Tests
```typescript
describe('Dashboard Integration', () => {
  it('should display Customer Insights stats', async () => {
    // Render Dashboard
    // Wait for stats to load
    // Verify Customer Insights card shows correct data
  });

  it('should navigate to history page', async () => {
    // Click on Customer Insights card
    // Verify navigation to /customer-insights/history
  });
});
```

---

## Troubleshooting

### Issue: Stats show 0 even with analyses
**Solution**: 
- Check backend is returning `segments_found` and `communities_found`
- Verify `customerInsightsApi.getHistory()` is being called
- Check browser console for errors

### Issue: TypeScript errors
**Solution**:
- Verify `customerInsights` is in `DashboardStats` interface
- Verify 'customer' is in `Activity` type union
- Run `npm run type-check`

### Issue: Navigation not working
**Solution**:
- Verify routes are defined in App.tsx
- Check onClick handlers in Dashboard.tsx
- Verify route paths match exactly

### Issue: Counts don't update after creating analysis
**Solution**:
- Implement refresh mechanism
- Check if `fetchStats()` is called after analysis completion
- Verify cache invalidation

---

## Success Criteria

All tests pass when:
- ✅ Customer Insights stats display correctly in Dashboard
- ✅ Segments and communities counts are accurate
- ✅ Recent activity includes Customer Insights
- ✅ Control Center shows correct count
- ✅ Profile page shows correct count
- ✅ All navigation links work
- ✅ No TypeScript errors
- ✅ No console errors
- ✅ Performance is acceptable
- ✅ Other modules still work correctly

---

**Testing Completed By**: _________________  
**Date**: _________________  
**Status**: [ ] Pass [ ] Fail  
**Notes**: _________________
