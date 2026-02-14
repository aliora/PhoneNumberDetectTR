#!/usr/bin/env python3
"""
Simple test script to verify the OCR microservice setup
"""

import sys
import time
import requests

RECEIVER_URL = "http://localhost:8001"
TEST_IMAGE_URL = "https://via.placeholder.com/800x600.png?text=Sözleşme-5356314848"

def test_receiver_health():
    """Test if receiver service is running"""
    print("🔍 Testing Receiver Service health...")
    try:
        response = requests.get(f"{RECEIVER_URL}/status", timeout=5)
        if response.ok:
            data = response.json()
            print(f"✅ Receiver is {data['status']}")
            print(f"   Redis: {'✅ Connected' if data['redis_connected'] else '❌ Disconnected'}")
            print(f"   Queue size: {data['queue_size']}")
            return True
        else:
            print(f"❌ Receiver returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Receiver: {e}")
        return False

def test_submit_job():
    """Test job submission"""
    print("\n📤 Testing job submission...")
    try:
        payload = {
            "image_url": TEST_IMAGE_URL,
            "user_id": "test_user",
            "timestamp": "2026-02-14T12:00:00"
        }
        
        response = requests.post(f"{RECEIVER_URL}/process", json=payload, timeout=10)
        
        if response.status_code == 202:
            data = response.json()
            task_id = data['task_id']
            print(f"✅ Job submitted successfully")
            print(f"   Task ID: {task_id}")
            print(f"   Status: {data['status']}")
            print(f"   Queue size: {data['queue_size']}")
            return task_id
        else:
            print(f"❌ Failed to submit job: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to submit job: {e}")
        return None

def test_query_result(task_id, max_wait=30):
    """Test result querying with polling"""
    print(f"\n🔎 Testing result query for task {task_id[:8]}...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{RECEIVER_URL}/result/{task_id}", timeout=5)
            
            if response.ok:
                data = response.json()
                status = data.get('status')
                
                if status == 'processing':
                    print(f"⏳ Still processing... ({int(time.time() - start_time)}s)")
                    time.sleep(2)
                    continue
                    
                elif status == 'completed':
                    result = data.get('result', {})
                    print(f"✅ Job completed successfully!")
                    print(f"   Phone: {result.get('phone_number', 'Not found')}")
                    print(f"   Confidence: {result.get('confidence', 0) * 100:.1f}%")
                    print(f"   Processing time: {result.get('processing_time')}s")
                    return True
                    
                elif status == 'error':
                    print(f"❌ Job failed with error: {data.get('error')}")
                    return False
                    
            else:
                print(f"❌ Query failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Query error: {e}")
            return False
    
    print(f"⏰ Timeout waiting for result ({max_wait}s)")
    return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("OCR Microservice Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_receiver_health():
        print("\n❌ Health check failed. Is the service running?")
        print("   Run: bash scripts/start_services.sh")
        sys.exit(1)
    
    # Test 2: Submit job
    task_id = test_submit_job()
    if not task_id:
        print("\n❌ Job submission failed")
        sys.exit(1)
    
    # Test 3: Query result
    if not test_query_result(task_id, max_wait=60):
        print("\n❌ Result query failed")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\n🌐 Open the Debug UI: http://localhost:5000")

if __name__ == "__main__":
    main()
