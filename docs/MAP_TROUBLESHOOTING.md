# 🗺️ Map Display Troubleshooting Guide

## Issue: Safety Map Not Displaying

If your safety map is not showing up, follow these troubleshooting steps:

## ✅ Quick Fixes

### 1. Check Dependencies
Make sure all required packages are installed:
```bash
pip install streamlit folium streamlit-folium
```

### 2. Verify Installation
Test if folium works:
```bash
python -c "import folium; print('Folium OK')"
```

### 3. Check Browser Console
- Open browser developer tools (F12)
- Check for JavaScript errors in Console tab
- Look for network errors in Network tab

### 4. Clear Streamlit Cache
```bash
streamlit cache clear
```

### 5. Use Debug Features
- Expand "🔍 Map Debug Info" in the app
- Click "🧪 Test Map Display" button
- Check error messages displayed

## 🔧 Enhanced Error Handling

The app now includes:

1. **Multiple Fallback Methods**:
   - Primary: `st_folium()` 
   - Fallback 1: HTML rendering via `st.components.v1.html()`
   - Fallback 2: Minimal map creation

2. **Detailed Error Messages**:
   - Each component (hazards, shelters, routes) has error handling
   - Errors are shown but don't stop map rendering
   - Full stack traces for critical errors

3. **Graceful Degradation**:
   - Map displays even if some components fail
   - Missing data doesn't prevent map from showing
   - Components added independently

## 🐛 Common Issues & Solutions

### Issue: Blank Map Area
**Possible Causes:**
- Network issues loading map tiles
- Browser blocking map content
- JavaScript disabled

**Solutions:**
- Check internet connection
- Try different browser
- Enable JavaScript
- Use offline mode toggle

### Issue: Map Shows but No Markers
**Possible Causes:**
- Data files missing or empty
- Coordinate errors
- Marker rendering failed

**Solutions:**
- Check data files in `data/` directory
- Verify coordinates are valid lat/lon
- Check error messages in app

### Issue: Map Crashes on Load
**Possible Causes:**
- Folium version incompatibility
- Memory issues
- Corrupt map object

**Solutions:**
- Update folium: `pip install --upgrade folium`
- Restart Streamlit app
- Clear browser cache

## 📋 Debug Checklist

- [ ] Folium installed: `pip list | grep folium`
- [ ] Streamlit-folium installed: `pip list | grep streamlit-folium`
- [ ] Map test button works
- [ ] No errors in browser console
- [ ] Network tab shows map tiles loading
- [ ] Error messages visible in app

## 🔍 Debug Info Location

The app includes a debug expander that shows:
- Center point coordinates
- Current state selection
- Offline mode status
- Data loading status (hazards, shelters)
- Test map button

## 🚀 If Map Still Doesn't Display

1. **Run Test Command**:
   ```bash
   python -c "import folium; m = folium.Map(location=[9.931, 76.267]); print(m._repr_html_()[:100])"
   ```

2. **Check Streamlit Version**:
   ```bash
   streamlit --version
   ```
   Should be >= 1.28.0

3. **Verify File Permissions**:
   - Ensure read access to all files
   - Check data directory exists

4. **Review Error Logs**:
   - Check terminal where Streamlit is running
   - Look for Python tracebacks
   - Check browser console for JS errors

## 💡 Pro Tips

1. **Start Simple**: The test map button creates a minimal map to verify rendering works

2. **Add Components Gradually**: 
   - First verify base map works
   - Then add origin point
   - Then add shelters
   - Finally add hazards and routes

3. **Use Offline Mode**: If network issues persist, toggle offline mode in sidebar

4. **Check Coordinates**: Ensure all coordinates are valid (lat: -90 to 90, lon: -180 to 180)

## 📞 Getting Help

If issues persist:
1. Capture full error message
2. Take screenshot of browser console
3. Note your Python and package versions
4. Check ENHANCEMENTS.md for recent changes

---

**The map should now display reliably with multiple fallback methods!** 🎉

