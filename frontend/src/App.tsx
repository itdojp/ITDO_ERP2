import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { AdminLayout } from '@/components/AdminLayout'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { UserListPage } from '@/pages/UserListPage'
import { OrganizationListPage } from '@/pages/OrganizationListPage'
import { DepartmentListPage } from '@/pages/DepartmentListPage'
import { TaskListPage } from '@/pages/TaskListPage'
import { PermissionListPage } from '@/pages/PermissionListPage'
import { ProjectListPage } from '@/pages/ProjectListPage'
import PrivateRoute from '@/components/PrivateRoute'
import './App.css'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<HomePage />} />
          
          {/* Protected routes */}
          <Route path="/dashboard" element={
            <PrivateRoute>
              <Layout>
                <DashboardPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/users" element={
            <PrivateRoute>
              <Layout>
                <UserListPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/organizations" element={
            <PrivateRoute>
              <Layout>
                <OrganizationListPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/departments" element={
            <PrivateRoute>
              <Layout>
                <DepartmentListPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/tasks" element={
            <PrivateRoute>
              <Layout>
                <TaskListPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/projects" element={
            <PrivateRoute>
              <Layout>
                <ProjectListPage />
              </Layout>
            </PrivateRoute>
          } />
          
          <Route path="/settings" element={
            <PrivateRoute>
              <Layout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold">Settings</h1>
                  <p className="text-gray-600">Coming soon...</p>
                </div>
              </Layout>
            </PrivateRoute>
          } />
          
          {/* Admin Routes */}
          <Route path="/admin" element={
            <PrivateRoute>
              <AdminLayout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold">Admin Dashboard</h1>
                  <p className="text-gray-600">System administration overview</p>
                </div>
              </AdminLayout>
            </PrivateRoute>
          } />
          
          <Route path="/admin/permissions" element={
            <PrivateRoute>
              <AdminLayout>
                <PermissionListPage />
              </AdminLayout>
            </PrivateRoute>
          } />
          
          <Route path="/admin/users" element={
            <PrivateRoute>
              <AdminLayout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold">User Management</h1>
                  <p className="text-gray-600">Manage system users and their roles</p>
                </div>
              </AdminLayout>
            </PrivateRoute>
          } />
          
          <Route path="/admin/organizations" element={
            <PrivateRoute>
              <AdminLayout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold">Organization Management</h1>
                  <p className="text-gray-600">Manage organizations and departments</p>
                </div>
              </AdminLayout>
            </PrivateRoute>
          } />
          
          <Route path="/admin/settings" element={
            <PrivateRoute>
              <AdminLayout>
                <div className="p-6">
                  <h1 className="text-2xl font-bold">System Settings</h1>
                  <p className="text-gray-600">Configure system-wide settings</p>
                </div>
              </AdminLayout>
            </PrivateRoute>
          } />
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}

export default App