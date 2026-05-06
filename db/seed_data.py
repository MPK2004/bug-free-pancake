import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

def seed():
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Clear existing data in correct order
        cur.execute("TRUNCATE TABLE category_insights, proposals, rental_agreements, tenants, malls CASCADE;")
        
        # Reset sequences if necessary (though TRUNCATE CASCADE usually does enough if no other activity)
        # But let's be explicit
        cur.execute("ALTER SEQUENCE malls_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE tenants_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE proposals_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE rental_agreements_id_seq RESTART WITH 1;")

        # 1. Seed Malls
        malls = [
            ("Mall of Istanbul",),
            ("Kanyon",),
            ("Metrocity",),
            ("Metropol AVM",),
            ("Istinye Park",),
            ("Zorlu Center",),
            ("Cevahir AVM",),
            ("Viaport Outlet",),
            ("Emaar Square Mall",),
            ("Forum Istanbul",)
        ]
        for mall in malls:
            cur.execute("INSERT INTO malls (name) VALUES (%s);", mall)

        # 2. Seed Tenants
        tenants = [
            ("Zara", "Clothing", "Premium"),
            ("H&M", "Clothing", "Mass"),
            ("Nike", "Shoes", "Premium"),
            ("Adidas", "Shoes", "Premium"),
            ("Samsung", "Technology", "Premium"),
            ("Apple", "Technology", "Luxury"),
            ("KFC", "Food & Beverage", "Mass"),
            ("Starbucks", "Food & Beverage", "Mass"),
            ("Sephora", "Cosmetics", "Premium"),
            ("Toyzz Shop", "Toys", "Mass")
        ]
        for tenant in tenants:
            cur.execute("INSERT INTO tenants (name, category, brand_type) VALUES (%s, %s, %s);", tenant)

        # 3. Seed Category Insights
        insights = [
            ("Clothing", "HIGH", "Dominant category across all malls. Prioritize for premium spots."),
            ("Shoes", "HIGH", "Strong secondary category. High demand in Istanbul and Kanyon."),
            ("Technology", "MEDIUM", "Stable demand. Good for diversification."),
            ("Cosmetics", "LOW", "Niche but premium."),
            ("Food & Beverage", "LOW", "High volume but lower revenue share."),
            ("Toys", "LOW", "Seasonal / target specific.")
        ]
        for insight in insights:
            cur.execute("INSERT INTO category_insights (category, priority, note) VALUES (%s, %s, %s);", insight)

        # 4. Seed Proposals (using IDs starting from 1)
        proposals = [
            (1, 1, 150000, 5000000), # Zara at Mall of Istanbul (Tenant 1, Mall 1)
            (3, 1, 80000, 2000000),  # Nike at Mall of Istanbul (Tenant 3, Mall 1)
            (5, 1, 120000, 3000000), # Samsung at Mall of Istanbul (Tenant 5, Mall 1)
            (1, 2, 140000, 4800000), # Zara at Kanyon (Tenant 1, Mall 2)
            (6, 2, 200000, 6000000), # Apple at Kanyon (Tenant 6, Mall 2)
            (7, 3, 50000, 1000000),  # KFC at Metrocity (Tenant 7, Mall 3)
        ]
        for prop in proposals:
            cur.execute("INSERT INTO proposals (tenant_id, mall_id, proposed_rent, expected_sales) VALUES (%s, %s, %s, %s);", prop)

        # 5. Seed Rental Agreements (Active Tenants)
        agreements = [
            (1, 1, 120000, 2.5, '2023-01-01', '2025-01-01', 'Active'), # Zara at Mall of Istanbul
            (2, 2, 90000, 3.0, '2023-05-01', '2026-05-01', 'Active'),  # H&M at Kanyon
            (3, 3, 70000, 2.0, '2023-02-01', '2025-02-01', 'Active'),  # Nike at Metrocity
            (4, 4, 65000, 2.0, '2023-03-01', '2025-03-01', 'Active'),  # Adidas at Metropol AVM
            (5, 5, 110000, 1.5, '2023-04-01', '2026-04-01', 'Active'), # Samsung at Istinye Park
            (6, 6, 180000, 1.0, '2023-06-01', '2027-06-01', 'Active'), # Apple at Zorlu Center
            (7, 7, 45000, 5.0, '2023-01-15', '2024-01-15', 'Active'),  # KFC at Cevahir AVM
            (8, 8, 40000, 6.0, '2023-02-15', '2024-02-15', 'Active'),  # Starbucks at Viaport Outlet
            (9, 9, 55000, 4.0, '2023-03-15', '2025-03-15', 'Active'),  # Sephora at Emaar Square Mall
            (10, 10, 30000, 0.0, '2023-04-15', '2025-04-15', 'Active') # Toyzz Shop at Forum Istanbul
        ]
        for agg in agreements:
            cur.execute("""
                INSERT INTO rental_agreements (tenant_id, mall_id, base_rent, revenue_share_percentage, start_date, end_date, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, agg)

        conn.commit()
        print("Database seeded successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed()
