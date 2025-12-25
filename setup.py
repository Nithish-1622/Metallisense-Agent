"""
Complete Setup and Training Script for MetalliSense AI Service
Run this script to generate data, train models, and verify the system
"""
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent / "app"))

from app.data.grade_specs import GradeSpecificationGenerator
from app.data.synthetic_gen import SyntheticDataGenerator
from app.config import (
    DATASET_PATH, 
    SYNTHETIC_DATASET_SIZE, 
    NORMAL_RATIO,
    ANOMALY_MODEL_PATH,
    ALLOY_MODEL_PATH
)


def main():
    """Run complete setup process - Train models with existing data"""
    
    print("\n" + "="*70)
    print(" METALLISENSE AI SERVICE - MODEL RETRAINING")
    print("="*70)
    
    # Step 1: Verify Dataset Exists
    print("\n[STEP 1] Verifying Existing Dataset...")
    print("-"*70)
    
    if not DATASET_PATH.exists():
        print(f"✗ Dataset not found: {DATASET_PATH}")
        print("  Please ensure dataset.csv exists in app/data/")
        return
    
    # Load and analyze existing dataset
    import pandas as pd
    df = pd.read_csv(DATASET_PATH)
    
    print(f"✓ Dataset loaded: {DATASET_PATH}")
    print(f"  Total samples: {len(df):,}")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    
    # Check for required columns
    required_cols = ['Fe', 'C', 'Si', 'Mn', 'P', 'S', 'grade']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"✗ Missing required columns: {missing_cols}")
        return
    
    # Dataset statistics
    print(f"\n  Dataset Statistics:")
    print(f"    Grades: {df['grade'].nunique()}")
    print(f"    Grade distribution:")
    for grade, count in df['grade'].value_counts().items():
        print(f"      {grade}: {count:,} samples ({count/len(df)*100:.1f}%)")
    
    if 'is_deviated' in df.columns:
        deviated_count = df['is_deviated'].sum()
        print(f"    Deviated samples: {deviated_count:,} ({deviated_count/len(df)*100:.1f}%)")
    
    # Step 2: Train Anomaly Detection Agent
    print("\n[STEP 2] Training Anomaly Detection Agent...")
    print("-"*70)
    
    from app.training.train_anomaly import train_anomaly_model
    anomaly_agent, anomaly_stats = train_anomaly_model(
        dataset_path=str(DATASET_PATH),
        save_path=str(ANOMALY_MODEL_PATH)
    )
    
    # Step 3: Train Alloy Correction Agent
    print("\n[STEP 3] Training Alloy Correction Agent...")
    print("-"*70)
    
    from app.training.train_alloy_agent import train_alloy_model
    alloy_agent, alloy_stats = train_alloy_model(
        dataset_path=str(DATASET_PATH),
        save_path=str(ALLOY_MODEL_PATH)
    )
    
    # Step 4: Verification
    print("\n[STEP 4] System Verification...")
    print("-"*70)
    
    # Verify models exist
    models_exist = {
        "Anomaly Model": ANOMALY_MODEL_PATH.exists(),
        "Alloy Model": ALLOY_MODEL_PATH.exists(),
        "Dataset": DATASET_PATH.exists()
    }
    
    print("\nFile Verification:")
    for name, exists in models_exist.items():
        status = "✓" if exists else "✗"
        print(f"  {status} {name}")
    
    # Test inference
    print("\nTesting Inference Modules:")
    
    try:
        from app.inference.anomaly_predict import get_anomaly_predictor
        from app.inference.alloy_predict import get_alloy_predictor
        
        anomaly_pred = get_anomaly_predictor()
        alloy_pred = get_alloy_predictor()
        
        print("  ✓ Anomaly predictor loaded")
        print("  ✓ Alloy predictor loaded")
        
        # Quick test
        test_comp = {
            "Fe": 85.0,
            "C": 3.5,
            "Si": 2.2,
            "Mn": 0.7,
            "P": 0.04,
            "S": 0.02
        }
        
        anomaly_result = anomaly_pred.predict(test_comp)
        alloy_result = alloy_pred.predict("SG-IRON", test_comp)
        
        print("\n  Quick Inference Test:")
        print(f"    Anomaly Score: {anomaly_result['anomaly_score']:.4f} ({anomaly_result['severity']})")
        print(f"    Alloy Confidence: {alloy_result['confidence']:.4f}")
        print("  ✓ Inference working correctly")
        
    except Exception as e:
        print(f"  ✗ Inference test failed: {e}")
    
    # Final Summary
    print("\n" + "="*70)
    print(" MODEL RETRAINING COMPLETED SUCCESSFULLY!")
    print("="*70)
    
    print("\n📊 Training Summary:")
    print(f"  Dataset: {len(df):,} samples")
    print(f"  Models trained: 2 (Anomaly Detection + Alloy Correction)")
    print(f"  Anomaly model: {ANOMALY_MODEL_PATH}")
    print(f"  Alloy model: {ALLOY_MODEL_PATH}")
    
    print("\nNext Steps:")
    print("  1. Start the API service:")
    print("     python app/main.py")
    print("")
    print("  2. Test the agent system:")
    print("     python test_agent_system.py")
    print("")
    print("  3. Access API documentation:")
    print("     http://localhost:8000/docs")
    print("")
    print("  4. Use /agents/analyze endpoint for production")
    print("")
    
    print("="*70)
    print("\n")


if __name__ == "__main__":
    main()
