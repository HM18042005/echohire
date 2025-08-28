# Firebase Firestore Setup Instructions

## Required Indexes for EchoHire

When using complex queries in Firestore, composite indexes are required for optimal performance. 

### Current Status
✅ **FIXED**: The backend has been updated to work without requiring a composite index by sorting results in Python instead of Firestore.

### For Optimal Performance (Optional)

If you want to enable server-side sorting for better performance with large datasets, you'll need to create the following composite index:

#### Index Configuration:
- **Collection**: `interviews`
- **Fields**:
  - `userId` (Ascending)
  - `interviewDate` (Descending)

#### How to Create the Index:

1. **Automatic Creation** (Recommended):
   - Visit the URL provided in the error message when it occurs
   - Click "Create Index" and wait for it to build

2. **Manual Creation**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project: `echohire-51478`
   - Navigate to Firestore Database → Indexes
   - Click "Create Index"
   - Set:
     - Collection ID: `interviews`
     - Field 1: `userId` (Ascending)
     - Field 2: `interviewDate` (Descending)
   - Click "Create"

#### Alternative URL (if needed):
```
https://console.firebase.google.com/v1/r/project/echohire-51478/firestore/indexes?create_composite=ClFwcm9qZWN0cy9lY2hvaGlyZS01MTQ3OC9kYXRhYmFzZXMvKGRlZmF1bHQpL2NvbGxlY3Rpb25Hcm91cHMvaW50ZXJ2aWV3cy9pbmRleGVzL18QARoKCgZ1c2VySWQQARoRCg1pbnRlcnZpZXdEYXRlEAIaDAoIX19uYW1lX18QAg
```

### After Index Creation

Once the index is created and active, you can update the backend code to use server-side sorting:

```python
# In backend/main.py, replace the simplified query with:
interviews_ref = db.collection("interviews").where("userId", "==", uid).order_by("interviewDate", direction=firestore.Query.DESCENDING)

# And remove the Python sorting:
# interview_list.sort(key=lambda x: x.interviewDate, reverse=True)
```

### Current Backend Implementation

The current implementation works without indexes by:
1. Querying all interviews for a user
2. Sorting results in Python using `interview_list.sort()`
3. This is suitable for small to medium datasets (< 1000 interviews per user)

### Performance Considerations

- **Without Index**: Works for all users, slower for large datasets
- **With Index**: Faster queries, especially for users with many interviews
- **Recommendation**: Create the index if you expect users to have > 50 interviews

### Error Resolution

The error you encountered:
```
The query requires an index. You can create it here: [URL]
```

Has been resolved by:
- ✅ Removing the server-side `order_by` clause
- ✅ Implementing client-side sorting in Python
- ✅ App now works without requiring index creation

The app is now fully functional for testing and development!
