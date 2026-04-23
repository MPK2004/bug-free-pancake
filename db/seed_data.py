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
