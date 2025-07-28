/**
 * プロジェクト一覧ページ
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Project,
  ListResponse,
  ProjectCreate,
} from "../../services/projectManagement";
import { projectManagementService } from "../../services/projectManagementExtended";
import { ProjectCard } from "../../components/project-management/ProjectCard";
import { ProjectForm } from "../../components/project-management/ProjectForm";
import {
  PlusIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";

export const ProjectListPage: React.FC = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(12);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: {
        skip: number;
        limit: number;
        search?: string;
        status?: string;
      } = {
        skip: (currentPage - 1) * pageSize,
        limit: pageSize,
      };

      if (searchTerm) {
        params.search = searchTerm;
      }

      if (statusFilter !== "all") {
        params.status = statusFilter;
      }

      const response: ListResponse<Project> =
        await projectManagementService.projects.list(params);
      setProjects(response.items);
      setTotalCount(response.total);
    } catch (err) {
      setError("プロジェクトの取得に失敗しました");
      // console.error('Failed to fetch projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, statusFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    fetchProjects();
  };

  const handleCreateProject = async (data: ProjectCreate) => {
    try {
      await projectManagementService.projects.create(data);
      setShowCreateForm(false);
      fetchProjects();
    } catch (err) {
      // console.error('Failed to create project:', err);
      alert("プロジェクトの作成に失敗しました");
    }
  };

  const handleProjectClick = (project: Project) => {
    navigate(`/projects/${project.id}`);
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">プロジェクト管理</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          新規プロジェクト
        </button>
      </div>

      {/* 検索・フィルター */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <form
          onSubmit={handleSearch}
          className="flex flex-col sm:flex-row gap-4"
        >
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="プロジェクト名で検索..."
                className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">すべて</option>
              <option value="planning">計画中</option>
              <option value="active">進行中</option>
              <option value="completed">完了</option>
              <option value="suspended">中断</option>
            </select>
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            検索
          </button>

          <button
            type="button"
            onClick={() => {
              setSearchTerm("");
              setStatusFilter("all");
              setCurrentPage(1);
              fetchProjects();
            }}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            <ArrowPathIcon className="h-5 w-5" />
          </button>
        </form>
      </div>

      {/* プロジェクト一覧 */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : error ? (
        <div className="bg-red-50 p-4 rounded-lg">
          <p className="text-red-600">{error}</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-gray-50 p-8 rounded-lg text-center">
          <p className="text-gray-500">プロジェクトが見つかりませんでした</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => handleProjectClick(project)}
              />
            ))}
          </div>

          {/* ページネーション */}
          {totalPages > 1 && (
            <div className="flex justify-center mt-8">
              <nav className="flex space-x-2">
                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.max(prev - 1, 1))
                  }
                  disabled={currentPage === 1}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  前へ
                </button>

                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((page) => {
                    const distance = Math.abs(page - currentPage);
                    return (
                      distance === 0 ||
                      distance === 1 ||
                      page === 1 ||
                      page === totalPages
                    );
                  })
                  .map((page, index, array) => {
                    if (index > 0 && array[index - 1] !== page - 1) {
                      return (
                        <React.Fragment key={`ellipsis-${page}`}>
                          <span className="px-3 py-2 text-gray-500">...</span>
                          <button
                            onClick={() => setCurrentPage(page)}
                            className={`px-3 py-2 text-sm font-medium rounded-md ${
                              currentPage === page
                                ? "bg-indigo-600 text-white"
                                : "text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                            }`}
                          >
                            {page}
                          </button>
                        </React.Fragment>
                      );
                    }
                    return (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`px-3 py-2 text-sm font-medium rounded-md ${
                          currentPage === page
                            ? "bg-indigo-600 text-white"
                            : "text-gray-700 bg-white border border-gray-300 hover:bg-gray-50"
                        }`}
                      >
                        {page}
                      </button>
                    );
                  })}

                <button
                  onClick={() =>
                    setCurrentPage((prev) => Math.min(prev + 1, totalPages))
                  }
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  次へ
                </button>
              </nav>
            </div>
          )}
        </>
      )}

      {/* プロジェクト作成モーダル */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                新規プロジェクト作成
              </h2>
              <ProjectForm
                projects={projects}
                onSubmit={handleCreateProject}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectListPage;
