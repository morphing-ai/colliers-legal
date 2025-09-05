// frontend/src/pages/AdminPage.tsx
import React, { useState, useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import {
  Loader2,
  Settings,
  Database,
  Trash2,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Input } from "../components/ui/input";

import { useToast } from "../hooks/useToast";

const AdminPage: React.FC = () => {
  const { getToken } = useAuth();
  const { toast } = useToast();

  const [loading, setLoading] = useState(false);
  const [cacheStatus, setCacheStatus] = useState<any>(null);
  const [cacheEnabled, setCacheEnabled] = useState(true);
  const [ttlHours, setTtlHours] = useState(24);

  useEffect(() => {
    fetchCacheStatus();
  }, []);

  const fetchCacheStatus = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/admin/cache/status`,
        {
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setCacheStatus(data);
        setCacheEnabled(data.cache_enabled);
        setTtlHours(data.ttl_hours);
      } else if (response.status === 403) {
        toast({
          title: "Access Denied",
          description: "Admin access required",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error fetching cache status:", error);
    } finally {
      setLoading(false);
    }
  };

  const updateCacheConfig = async () => {
    try {
      const token = await getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/admin/cache/configure`,
        {
          method: "POST",
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            enabled: cacheEnabled,
            ttl_hours: ttlHours,
          }),
        }
      );

      if (response.ok) {
        toast({
          title: "Success",
          description: `Cache ${
            cacheEnabled ? "enabled" : "disabled"
          } with ${ttlHours}h TTL`,
        });
        fetchCacheStatus();
      }
    } catch (error) {
      console.error("Error updating cache config:", error);
      toast({
        title: "Error",
        description: "Failed to update cache configuration",
        variant: "destructive",
      });
    }
  };

  const clearCache = async (expiredOnly: boolean = false) => {
    try {
      const token = await getToken();
      const response = await fetch(
        `${
          import.meta.env.VITE_API_URL
        }/admin/cache/clear?expired_only=${expiredOnly}`,
        {
          method: "POST",
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast({
          title: "Cache Cleared",
          description: data.message,
        });
        fetchCacheStatus();
      }
    } catch (error) {
      console.error("Error clearing cache:", error);
      toast({
        title: "Error",
        description: "Failed to clear cache",
        variant: "destructive",
      });
    }
  };

  const cleanupAnalyses = async () => {
    if (
      !confirm(
        "This will delete all analyses with invalid/hallucinated rule numbers. Continue?"
      )
    ) {
      return;
    }

    try {
      const token = await getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/admin/analyses/cleanup`,
        {
          method: "DELETE",
          headers: {
            Authorization: token ? `Bearer ${token}` : "",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        toast({
          title: "Cleanup Complete",
          description: data.message,
        });
      }
    } catch (error) {
      console.error("Error cleaning analyses:", error);
      toast({
        title: "Error",
        description: "Failed to cleanup analyses",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-2">
          Admin Panel
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-300">
          System configuration and maintenance
        </p>
      </div>

      {/* Cache Configuration */}
      <Card className="mb-6 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Database className="h-5 w-5" />
          <h2 className="text-xl font-semibold">Cache Configuration</h2>
        </div>

        {cacheStatus && (
          <div className="space-y-4">
            {/* Cache Statistics */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
              <div>
                <p className="text-sm text-slate-500">Total Entries</p>
                <p className="text-2xl font-bold">
                  {cacheStatus.total_entries}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Valid Entries</p>
                <p className="text-2xl font-bold text-green-600">
                  {cacheStatus.valid_entries}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Expired Entries</p>
                <p className="text-2xl font-bold text-red-600">
                  {cacheStatus.expired_entries}
                </p>
              </div>
            </div>

            {/* Cache Settings */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="cache-enabled">Cache Enabled</Label>
                <button
                  onClick={() => setCacheEnabled(!cacheEnabled)}
                  className="flex items-center gap-2"
                >
                  {cacheEnabled ? (
                    <ToggleRight className="h-8 w-8 text-green-600" />
                  ) : (
                    <ToggleLeft className="h-8 w-8 text-slate-400" />
                  )}
                  <span className="text-sm font-medium">
                    {cacheEnabled ? "ON" : "OFF"}
                  </span>
                </button>
              </div>

              <div className="flex items-center gap-4">
                <Label htmlFor="ttl-hours">TTL (hours)</Label>
                <Input
                  id="ttl-hours"
                  type="number"
                  value={ttlHours}
                  onChange={(e) => setTtlHours(parseInt(e.target.value) || 24)}
                  className="w-24"
                  min="1"
                  max="168"
                />
              </div>

              <Button onClick={updateCacheConfig} className="w-full">
                <Settings className="h-4 w-4 mr-2" />
                Apply Configuration
              </Button>
            </div>

            {/* Cache Actions */}
            <div className="flex gap-2">
              <Button
                onClick={() => clearCache(true)}
                variant="outline"
                className="flex-1"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear Expired
              </Button>
              <Button
                onClick={() => clearCache(false)}
                variant="destructive"
                className="flex-1"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear All Cache
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Database Cleanup */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="h-5 w-5" />
          <h2 className="text-xl font-semibold">Database Maintenance</h2>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Remove analyses that contain invalid or hallucinated rule numbers
          </p>
          <Button
            onClick={cleanupAnalyses}
            variant="outline"
            className="w-full"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Cleanup Invalid Analyses
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AdminPage;
