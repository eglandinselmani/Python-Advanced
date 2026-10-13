import type { Recipe, Category, DashboardStats } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Mock data for UI development (will be replaced with API calls)
export const mockCategories: Category[] = [
  { id: '1', name: 'Breakfast', description: 'Morning meals', recipeCount: 5 },
  { id: '2', name: 'Lunch', description: 'Midday meals', recipeCount: 8 },
  { id: '3', name: 'Dinner', description: 'Evening meals', recipeCount: 12 },
  { id: '4', name: 'Desserts', description: 'Sweet treats', recipeCount: 6 },
  { id: '5', name: 'Snacks', description: 'Light bites', recipeCount: 4 },
]

export const mockRecipes: Recipe[] = [
  {
    id: '1',
    title: 'Classic Pancakes',
    description: 'Fluffy buttermilk pancakes perfect for breakfast',
    ingredients: ['2 cups flour', '2 tbsp sugar', '2 tsp baking powder', '1 tsp salt', '2 eggs', '1.5 cups milk', '4 tbsp butter'],
    instructions: ['Mix dry ingredients', 'Whisk eggs with milk and butter', 'Combine wet and dry ingredients', 'Cook on griddle until golden'],
    category: 'Breakfast',
    prepTime: 10,
    cookTime: 15,
    servings: 4,
    difficulty: 'Easy',
    imageUrl: 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=300&fit=crop',
    createdAt: new Date(Date.now() - 86400000 * 7).toISOString(),
    updatedAt: new Date(Date.now() - 86400000 * 7).toISOString(),
  },
  {
    id: '2',
    title: 'Grilled Salmon',
    description: 'Fresh grilled salmon with lemon and herbs',
    ingredients: ['2 salmon fillets', '2 lemons', 'olive oil', 'dill', 'salt', 'pepper'],
    instructions: ['Preheat grill', 'Season salmon with herbs and salt', 'Grill for 6-8 minutes per side', 'Serve with lemon'],
    category: 'Dinner',
    prepTime: 15,
    cookTime: 16,
    servings: 2,
    difficulty: 'Medium',
    imageUrl: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop',
    createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
    updatedAt: new Date(Date.now() - 86400000 * 3).toISOString(),
  },
  {
    id: '3',
    title: 'Chocolate Cake',
    description: 'Rich and decadent chocolate layer cake',
    ingredients: ['2 cups flour', '2 cups sugar', '3/4 cup cocoa powder', '2 tsp baking soda', '1 tsp baking powder', '1 tsp salt', '2 eggs', '1 cup buttermilk', '1 cup coffee', '1/2 cup oil', '1 tsp vanilla'],
    instructions: ['Preheat oven to 350F', 'Mix all dry ingredients', 'Combine wet ingredients separately', 'Mix together gently', 'Bake for 30-35 minutes', 'Cool before frosting'],
    category: 'Desserts',
    prepTime: 30,
    cookTime: 35,
    servings: 12,
    difficulty: 'Medium',
    imageUrl: 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&h=300&fit=crop',
    createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
    updatedAt: new Date(Date.now() - 86400000 * 2).toISOString(),
  },
  {
    id: '4',
    title: 'Caesar Salad',
    description: 'Classic Caesar salad with crispy croutons',
    ingredients: ['1 romaine lettuce', '1/2 cup parmesan', 'croutons', 'caesar dressing', 'lemon', 'black pepper'],
    instructions: ['Wash and chop romaine', 'Toss with caesar dressing', 'Add croutons and parmesan', 'Serve immediately'],
    category: 'Lunch',
    prepTime: 10,
    cookTime: 0,
    servings: 2,
    difficulty: 'Easy',
    imageUrl: 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop',
    createdAt: new Date(Date.now() - 86400000 * 1).toISOString(),
    updatedAt: new Date(Date.now() - 86400000 * 1).toISOString(),
  },
]

// Recipe API functions
export async function fetchRecipes(): Promise<Recipe[]> {
  try {
    const response = await fetch(`${API_URL}/recipes`)
    if (!response.ok) return mockRecipes
    return await response.json()
  } catch {
    return mockRecipes
  }
}

export async function fetchRecipeById(id: string): Promise<Recipe | null> {
  try {
    const response = await fetch(`${API_URL}/recipes/${id}`)
    if (!response.ok) return mockRecipes.find(r => r.id === id) || null
    return await response.json()
  } catch {
    return mockRecipes.find(r => r.id === id) || null
  }
}

export async function createRecipe(recipe: Omit<Recipe, 'id' | 'createdAt' | 'updatedAt'>): Promise<Recipe> {
  try {
    const response = await fetch(`${API_URL}/recipes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipe),
    })
    if (!response.ok) throw new Error('Failed to create recipe')
    return await response.json()
  } catch {
    return {
      ...recipe,
      id: Math.random().toString(36).substr(2, 9),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
  }
}

export async function updateRecipe(id: string, recipe: Partial<Recipe>): Promise<Recipe> {
  try {
    const response = await fetch(`${API_URL}/recipes/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recipe),
    })
    if (!response.ok) throw new Error('Failed to update recipe')
    return await response.json()
  } catch {
    const existing = mockRecipes.find(r => r.id === id)
    return existing ? { ...existing, ...recipe, updatedAt: new Date().toISOString() } : ({} as Recipe)
  }
}

export async function deleteRecipe(id: string): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/recipes/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Failed to delete recipe')
  } catch {
    console.error('Delete recipe error')
  }
}

// Category API functions
export async function fetchCategories(): Promise<Category[]> {
  try {
    const response = await fetch(`${API_URL}/categories`)
    if (!response.ok) return mockCategories
    return await response.json()
  } catch {
    return mockCategories
  }
}

export async function createCategory(category: Omit<Category, 'id' | 'recipeCount'>): Promise<Category> {
  try {
    const response = await fetch(`${API_URL}/categories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(category),
    })
    if (!response.ok) throw new Error('Failed to create category')
    return await response.json()
  } catch {
    return {
      ...category,
      id: Math.random().toString(36).substr(2, 9),
      recipeCount: 0,
    }
  }
}

export async function updateCategory(id: string, category: Partial<Category>): Promise<Category> {
  try {
    const response = await fetch(`${API_URL}/categories/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(category),
    })
    if (!response.ok) throw new Error('Failed to update category')
    return await response.json()
  } catch {
    const existing = mockCategories.find(c => c.id === id)
    return existing ? { ...existing, ...category } : ({} as Category)
  }
}

export async function deleteCategory(id: string): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/categories/${id}`, { method: 'DELETE' })
    if (!response.ok) throw new Error('Failed to delete category')
  } catch {
    console.error('Delete category error')
  }
}

// Dashboard stats
export async function fetchDashboardStats(): Promise<DashboardStats> {
  const recipes = await fetchRecipes()
  const categories = await fetchCategories()
  
  const sorted = [...recipes].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  
  return {
    totalRecipes: recipes.length,
    totalCategories: categories.length,
    recentRecipes: sorted.slice(0, 3),
    popularRecipes: recipes.slice(0, 3),
  }
}
