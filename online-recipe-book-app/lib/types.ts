export interface Recipe {
  id: string
  title: string
  description: string
  ingredients: string[]
  instructions: string[]
  category: string
  prepTime: number
  cookTime: number
  servings: number
  difficulty: 'Easy' | 'Medium' | 'Hard'
  imageUrl?: string
  createdAt: string
  updatedAt: string
}

export interface Category {
  id: string
  name: string
  description?: string
  recipeCount: number
}

export interface DashboardStats {
  totalRecipes: number
  totalCategories: number
  recentRecipes: Recipe[]
  popularRecipes: Recipe[]
}
