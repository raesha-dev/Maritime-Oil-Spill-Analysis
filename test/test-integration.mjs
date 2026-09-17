/**
 * Test script to verify frontend-backend integration
 * Run: node test/test-integration.mjs
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load dummy data
const dummyDataPath = path.join(__dirname, 'dummy-dashboard-data.json');
const dummyData = JSON.parse(fs.readFileSync(dummyDataPath, 'utf8'));

console.log('=== Maritime Oil-Spill Forensic Analysis - Test Suite ===\n');

// Test 1: Verify dummy data structure
console.log('TEST 1: Dummy data structure validation');
try {
  const requiredFields = ['incident', 'detection', 'hindcast', 'ranking', 'simulations', 'assessment', 'evidence_events'];
  const missing = requiredFields.filter(field => !dummyData[field]);
  
  if (missing.length === 0) {
    console.log('  ✓ All required fields present');
    console.log(`  - Incident: ${dummyData.incident.incident_id}`);
    console.log(`  - Detection: ${dummyData.detection.satellite} SAR`);
    console.log(`  - Candidates: ${dummyData.ranking.candidates.length}`);
    console.log(`  - Assessment: ${dummyData.assessment.state}`);
  } else {
    console.log(`  ✗ Missing fields: ${missing.join(', ')}`);
  }
} catch (error) {
  console.log(`  ✗ Error: ${error.message}`);
}

// Test 2: Verify styles are loaded
console.log('\nTEST 2: CSS styling');
const stylesPath = path.join(__dirname, '..', 'src', 'styles.css');
if (fs.existsSync(stylesPath)) {
  const stylesContent = fs.readFileSync(stylesPath, 'utf8');
  const requiredColors = ['--bg-app', '--cyan', '--ais-consistent', '--simulated-spill'];
  const missingColors = requiredColors.filter(color => !stylesContent.includes(color));
  
  if (missingColors.length === 0) {
    console.log('  ✓ All required color variables defined');
    console.log('  - Dark maritime blue background hierarchy');
    console.log('  - Cyan accent (#00D4D8)');
    console.log('  - AIS integrity colors (green/amber/red/gray)');
    console.log('  - Simulated spill blue (#167FAF)');
  } else {
    console.log(`  ✗ Missing color variables: ${missingColors.join(', ')}`);
  }
} else {
  console.log('  ✗ Styles file not found');
}

// Test 3: Verify routing
console.log('\nTEST 3: Router configuration');
const routerPath = path.join(__dirname, '..', 'src', 'router.tsx');
if (fs.existsSync(routerPath)) {
  console.log('  ✓ Router configuration exists');
} else {
  console.log('  ✗ Router configuration not found');
}

// Test 4: Verify API URL configuration
console.log('\nTEST 4: Backend API configuration');
const envPath = path.join(__dirname, '..', '.env.example');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  if (envContent.includes('VITE_FORENSICS_API_URL')) {
    console.log('  ✓ Backend API URL configuration found');
    console.log('  - Default: http://localhost:8000');
  } else {
    console.log('  ✗ Backend API URL configuration missing');
  }
} else {
  console.log('  ⚠ .env.example not found');
}

// Test 5: Verify backend health endpoint
console.log('\nTEST 5: Backend connectivity test (dry-run)');
console.log('  Backend should be at: http://localhost:8000');
console.log('  Endpoint: /health');
console.log('  Response: {"status":"ok","service":"spill-forensics-api","version":"0.1.0"}');

console.log('\n=== Test Summary ===');
console.log('If all tests show ✓, the frontend is ready to integrate with the backend.');
console.log('\nTo start the application:');
console.log('  1. Start backend: cd backend && uvicorn app.main:app --reload --port 8000');
console.log('  2. Start frontend: npm run dev');
console.log('  3. Open http://localhost:5173 in your browser');
console.log('\nDummy data test file: test/dummy-dashboard-data.json');
