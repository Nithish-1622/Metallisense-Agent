"""
Quick Model Retraining Script
Retrain both models with existing dataset.csv
"""
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent / "app"))

from app.config import DATASET_PATH, ANOMALY_MODEL_PATH, ALLOY_MODEL_PATH
import pandas as pd


def retrain_models():
    """Retrain both models with existing data"""
    
    print("\n" + "="*70)
    print(" 🔄 QUICK MODEL RETRAINING")
    print("="*70)
    
    # Check dataset exists
    if not DATASET_PATH.exists():
        print(f"\n❌ Dataset not found: {DATASET_PATH}")
        print("Please ensure dataset.csv exists in app/data/")
        return False
    
    # Load dataset
    print(f"\n📊 Loading dataset from: {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)
    print(f"✓ Loaded {len(df):,} samples")
    
    # Train Anomaly Model
    print("\n" + "-"*70)
    print("🤖 Training Anomaly Detection Model...")
    print("-"*70)
    
    from app.training.train_anomaly import train_anomaly_model
    
    try:
        anomaly_agent, anomaly_stats = train_anomaly_model(
            dataset_path=str(DATASET_PATH),
            save_path=str(ANOMALY_MODEL_PATH)
        )
        print(f"✓ Anomaly model saved: {ANOMALY_MODEL_PATH}")
    except Exception as e:
        print(f"❌ Anomaly training failed: {e}")
        return False
    
    # Train Alloy Model
    print("\n" + "-"*70)
    print("🔧 Training Alloy Correction Model...")
    print("-"*70)
    
    from app.training.train_alloy_agent import train_alloy_model
    
    try:
        alloy_agent, alloy_stats = train_alloy_model(
            dataset_path=str(DATASET_PATH),
            save_path=str(ALLOY_MODEL_PATH)
        )
        print(f"✓ Alloy model saved: {ALLOY_MODEL_PATH}")
    except Exception as e:
        print(f"❌ Alloy training failed: {e}")
        return False
    
    # Success
    print("\n" + "="*70)
    print(" ✅ RETRAINING COMPLETE!")
    print("="*70)
    
    print("\n📈 Results:")
    print(f"  Samples used: {len(df):,}")
    print(f"  Anomaly model: ✓ Trained")
    print(f"  Alloy model: ✓ Trained")
    
    print("\n🚀 Ready to use! Start the API:")
    print("  python app/main.py")
    print("\n" + "="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = retrain_models()
    sys.exit(0 if success else 1)
