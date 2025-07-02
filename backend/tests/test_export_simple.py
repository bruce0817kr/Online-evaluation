"""
Simple test to verify export functionality without requiring full auth setup
"""
from export_utils import exporter
import asyncio
from datetime import datetime

async def test_export_functions():
    print("🧪 Testing Export Functions")
    print("=" * 40)
    
    # Test data
    test_evaluation_data = {
        "evaluation": {
            "id": "test_123",
            "submitted_at": datetime.now().isoformat(),
            "total_score": 85,
            "max_score": 100
        },
        "template": {
            "name": "테스트 평가표",
            "items": [
                {"id": "item1", "text": "기술력 평가", "max_score": 50},
                {"id": "item2", "text": "사업성 평가", "max_score": 30},
                {"id": "item3", "text": "팀 역량 평가", "max_score": 20}
            ]
        },
        "company": {
            "name": "테스트 기업"
        },
        "project": {
            "name": "테스트 프로젝트"
        },
        "evaluator": {
            "name": "테스트 평가위원"
        },
        "scores": [
            {"item_id": "item1", "score": 42, "opinion": "우수한 기술력을 보유하고 있음"},
            {"item_id": "item2", "score": 25, "opinion": "사업성이 양호함"},
            {"item_id": "item3", "score": 18, "opinion": "팀 구성이 잘 되어 있음"}
        ]
    }
    
    try:
        # Test filename generation
        print("📁 Testing filename generation...")
        filename = exporter.generate_filename(
            company_name="테스트 기업",
            project_name="테스트 프로젝트", 
            format_type="pdf"
        )
        print(f"✅ Generated filename: {filename}")
        
        # Test PDF export
        print("\n📄 Testing PDF export...")
        pdf_buffer = await exporter.export_single_evaluation_pdf(test_evaluation_data)
        
        if pdf_buffer and len(pdf_buffer.getvalue()) > 0:
            print(f"✅ PDF generated successfully! Size: {len(pdf_buffer.getvalue())} bytes")
            
            # Save test PDF
            with open("test_export_sample.pdf", "wb") as f:
                f.write(pdf_buffer.getvalue())
            print("   Sample PDF saved as: test_export_sample.pdf")
        else:
            print("❌ PDF generation failed!")
            
        # Test Excel export  
        print("\n📊 Testing Excel export...")
        excel_buffer = await exporter.export_single_evaluation_excel(test_evaluation_data)
        
        if excel_buffer and len(excel_buffer.getvalue()) > 0:
            print(f"✅ Excel generated successfully! Size: {len(excel_buffer.getvalue())} bytes")
            
            # Save test Excel
            with open("test_export_sample.xlsx", "wb") as f:
                f.write(excel_buffer.getvalue())
            print("   Sample Excel saved as: test_export_sample.xlsx")
        else:
            print("❌ Excel generation failed!")
            
        print("\n" + "=" * 40)
        print("✅ Export functionality test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_export_functions())
