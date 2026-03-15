import { useEffect, useMemo, useState, type FormEvent } from "react";

import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { SectionCard } from "@/components/SectionCard";
import { StatusBadge } from "@/components/StatusBadge";
import type {
  VirtualMachineCreatePayload,
  VirtualMachineRecord,
  VirtualMachineStatus,
} from "@/types/domain";
import {
  createVirtualLabMachine,
  fetchVirtualLabMachines,
  patchVirtualLabMachine,
} from "@/services/api";

type VirtualLabSectionProps = {
  token: string | null;
  canManage: boolean;
  refreshKey: number;
  onLabUpdated?: () => void;
};

const virtualMachineStatusOptions: VirtualMachineStatus[] = [
  "running",
  "paused",
  "stopped",
  "provisioning",
];

const defaultVirtualMachineForm: VirtualMachineCreatePayload = {
  vm_name: "",
  role: "",
  os_type: "",
  ip_address: "",
  status: "provisioning",
  notes: "",
};

function formatLabel(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function buildVirtualMachineForm(vm: VirtualMachineRecord): VirtualMachineCreatePayload {
  return {
    vm_name: vm.vm_name,
    role: vm.role,
    os_type: vm.os_type,
    ip_address: vm.ip_address,
    status: vm.status,
    notes: vm.notes,
  };
}

export function VirtualLabSection({
  token,
  canManage,
  refreshKey,
  onLabUpdated,
}: VirtualLabSectionProps) {
  const [virtualMachines, setVirtualMachines] = useState<VirtualMachineRecord[]>([]);
  const [selectedVmId, setSelectedVmId] = useState<string | null>(null);
  const [selectedVmDraft, setSelectedVmDraft] = useState<VirtualMachineCreatePayload | null>(null);
  const [newVmForm, setNewVmForm] = useState<VirtualMachineCreatePayload>(defaultVirtualMachineForm);
  const [labError, setLabError] = useState<string | null>(null);
  const [labMessage, setLabMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeAction, setActiveAction] = useState<"create" | "update" | null>(null);
  const [localRefreshKey, setLocalRefreshKey] = useState(0);

  useEffect(() => {
    if (!token) {
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setLabError(null);

    void fetchVirtualLabMachines(token)
      .then((labMachines) => {
        if (!isActive) {
          return;
        }

        setVirtualMachines(labMachines);
      })
      .catch((requestError: unknown) => {
        if (!isActive) {
          return;
        }

        setLabError(
          requestError instanceof Error
            ? requestError.message
            : "The VirtualBox lab inventory could not be loaded.",
        );
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [localRefreshKey, refreshKey, token]);

  useEffect(() => {
    if (!virtualMachines.length) {
      setSelectedVmId(null);
      setSelectedVmDraft(null);
      return;
    }

    const matchingVm =
      virtualMachines.find((virtualMachine) => virtualMachine.id === selectedVmId) ??
      virtualMachines[0];

    setSelectedVmId(matchingVm.id);
    setSelectedVmDraft(buildVirtualMachineForm(matchingVm));
  }, [selectedVmId, virtualMachines]);

  const selectedVm = useMemo(
    () => virtualMachines.find((virtualMachine) => virtualMachine.id === selectedVmId) ?? null,
    [selectedVmId, virtualMachines],
  );

  const labSummary = useMemo(() => {
    const running = virtualMachines.filter((vm) => vm.status === "running").length;
    const paused = virtualMachines.filter((vm) => vm.status === "paused").length;
    const provisioning = virtualMachines.filter((vm) => vm.status === "provisioning").length;

    return {
      total: virtualMachines.length,
      running,
      paused,
      provisioning,
    };
  }, [virtualMachines]);

  const virtualMachineColumns = useMemo<DataTableColumn<VirtualMachineRecord>[]>(
    () => [
      {
        key: "vm_name",
        header: "VM",
        render: (row) => (
          <div>
            <p className="font-semibold text-brand-black">{row.vm_name}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.16em] text-brand-black/45">
              {row.os_type}
            </p>
          </div>
        ),
      },
      {
        key: "role",
        header: "Role",
        render: (row) => <span className="font-medium text-brand-black/75">{row.role}</span>,
      },
      {
        key: "status",
        header: "Status",
        render: (row) => <StatusBadge variant={row.status}>{formatLabel(row.status)}</StatusBadge>,
      },
      {
        key: "ip_address",
        header: "IP Placeholder",
        render: (row) => (
          <span className="rounded-full bg-brand-light px-3 py-1 font-mono text-xs text-brand-black/70">
            {row.ip_address}
          </span>
        ),
      },
      {
        key: "notes",
        header: "Notes",
        render: (row) => <p className="max-w-[24rem] leading-6 text-brand-black/65">{row.notes}</p>,
      },
    ],
    [],
  );

  const handleCreateVm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      return;
    }

    setActiveAction("create");
    setLabError(null);
    setLabMessage(null);

    try {
      const createdVm = await createVirtualLabMachine(token, newVmForm);
      setLabMessage(`${createdVm.vm_name} was added to the lab inventory.`);
      setNewVmForm(defaultVirtualMachineForm);
      setSelectedVmId(createdVm.id);
      setLocalRefreshKey((currentValue) => currentValue + 1);
      onLabUpdated?.();
    } catch (requestError) {
      setLabError(
        requestError instanceof Error ? requestError.message : "The lab VM could not be added.",
      );
    } finally {
      setActiveAction(null);
    }
  };

  const handleUpdateVm = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token || !selectedVmId || !selectedVmDraft) {
      return;
    }

    setActiveAction("update");
    setLabError(null);
    setLabMessage(null);

    try {
      const updatedVm = await patchVirtualLabMachine(token, selectedVmId, selectedVmDraft);
      setLabMessage(`${updatedVm.vm_name} was updated in the lab inventory.`);
      setLocalRefreshKey((currentValue) => currentValue + 1);
      onLabUpdated?.();
    } catch (requestError) {
      setLabError(
        requestError instanceof Error ? requestError.message : "The selected VM could not be updated.",
      );
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <SectionCard
      title="Virtual lab environment"
      description="Track the VirtualBox-based classroom topology used for AegisCore validation, incident walkthroughs, and demo readiness."
      eyebrow="VirtualBox"
    >
      {labError ? (
        <div className="rounded-[1.5rem] border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
          {labError}
        </div>
      ) : null}

      {labMessage ? (
        <div className="rounded-[1.5rem] border border-brand-orange/15 bg-brand-orange/5 px-4 py-4 text-sm text-brand-black/75">
          {labMessage}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {virtualMachines.map((virtualMachine) => (
          <button
            key={virtualMachine.id}
            type="button"
            onClick={() => setSelectedVmId(virtualMachine.id)}
            className={`rounded-[1.5rem] border bg-white p-5 text-left shadow-sm transition ${selectedVmId === virtualMachine.id ? "border-brand-orange/30 ring-2 ring-brand-orange/15" : "border-brand-black/8 hover:border-brand-orange/20"}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-lg font-semibold text-brand-black">{virtualMachine.vm_name}</p>
                <p className="mt-1 text-sm text-brand-black/55">{virtualMachine.role}</p>
              </div>
              <StatusBadge variant={virtualMachine.status}>
                {formatLabel(virtualMachine.status)}
              </StatusBadge>
            </div>
            <div className="mt-4 space-y-2 text-sm text-brand-black/68">
              <p>{virtualMachine.os_type}</p>
              <p className="font-mono text-xs text-brand-black/55">{virtualMachine.ip_address}</p>
              <p className="leading-6">{virtualMachine.notes}</p>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
        <div className="space-y-4">
          <div className="rounded-[1.5rem] border border-brand-black/8 bg-white p-4">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-[1.25rem] bg-brand-light/70 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Tracked</p>
                <p className="mt-2 text-2xl font-semibold text-brand-black">{labSummary.total}</p>
              </div>
              <div className="rounded-[1.25rem] bg-brand-light/70 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Running</p>
                <p className="mt-2 text-2xl font-semibold text-brand-black">{labSummary.running}</p>
              </div>
              <div className="rounded-[1.25rem] bg-brand-light/70 px-4 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-brand-black/45">Paused / Provisioning</p>
                <p className="mt-2 text-2xl font-semibold text-brand-black">
                  {labSummary.paused + labSummary.provisioning}
                </p>
              </div>
            </div>
          </div>

          <DataTable
            columns={virtualMachineColumns}
            rows={virtualMachines}
            rowKey={(row) => row.id}
            selectedRowKey={selectedVmId ?? undefined}
            onRowClick={(row) => setSelectedVmId(row.id)}
            emptyMessage={isLoading ? "Loading lab inventory..." : "No lab VMs have been recorded yet."}
          />

          <div className="rounded-[1.5rem] border border-brand-black/8 bg-brand-light/60 px-4 py-4 text-sm leading-6 text-brand-black/65">
            VirtualBox support is limited to inventory tracking and environment visualization for the authorized lab. AegisCore does not directly control, start, stop, or orchestrate VMs in this scaffold.
          </div>
        </div>

        <div className="space-y-4">
          <form className="panel p-5" onSubmit={handleUpdateVm}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-orange">
                  Selected VM
                </p>
                <h3 className="mt-2 text-xl font-semibold text-brand-black">
                  {selectedVm?.vm_name ?? "No VM selected"}
                </h3>
              </div>
              {selectedVm ? (
                <StatusBadge variant={selectedVm.status}>{formatLabel(selectedVm.status)}</StatusBadge>
              ) : null}
            </div>

            {selectedVm && selectedVmDraft ? (
              <div className="mt-5 space-y-4">
                <label className="block text-sm font-medium text-brand-black">
                  VM name
                  <input
                    type="text"
                    value={selectedVmDraft.vm_name}
                    onChange={(event) =>
                      setSelectedVmDraft((currentValue) =>
                        currentValue ? { ...currentValue, vm_name: event.target.value } : currentValue,
                      )
                    }
                    className="input-shell mt-2 w-full bg-brand-light outline-none"
                    disabled={!canManage}
                  />
                </label>

                <label className="block text-sm font-medium text-brand-black">
                  Role
                  <input
                    type="text"
                    value={selectedVmDraft.role}
                    onChange={(event) =>
                      setSelectedVmDraft((currentValue) =>
                        currentValue ? { ...currentValue, role: event.target.value } : currentValue,
                      )
                    }
                    className="input-shell mt-2 w-full bg-brand-light outline-none"
                    disabled={!canManage}
                  />
                </label>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block text-sm font-medium text-brand-black">
                    OS type
                    <input
                      type="text"
                      value={selectedVmDraft.os_type}
                      onChange={(event) =>
                        setSelectedVmDraft((currentValue) =>
                          currentValue ? { ...currentValue, os_type: event.target.value } : currentValue,
                        )
                      }
                      className="input-shell mt-2 w-full bg-brand-light outline-none"
                      disabled={!canManage}
                    />
                  </label>

                  <label className="block text-sm font-medium text-brand-black">
                    IP placeholder
                    <input
                      type="text"
                      value={selectedVmDraft.ip_address}
                      onChange={(event) =>
                        setSelectedVmDraft((currentValue) =>
                          currentValue
                            ? { ...currentValue, ip_address: event.target.value }
                            : currentValue,
                        )
                      }
                      className="input-shell mt-2 w-full bg-brand-light outline-none"
                      disabled={!canManage}
                    />
                  </label>
                </div>

                <label className="block text-sm font-medium text-brand-black">
                  Status
                  <select
                    value={selectedVmDraft.status}
                    onChange={(event) =>
                      setSelectedVmDraft((currentValue) =>
                        currentValue
                          ? {
                              ...currentValue,
                              status: event.target.value as VirtualMachineStatus,
                            }
                          : currentValue,
                      )
                    }
                    className="input-shell mt-2 w-full bg-brand-light outline-none"
                    disabled={!canManage}
                  >
                    {virtualMachineStatusOptions.map((statusValue) => (
                      <option key={statusValue} value={statusValue}>
                        {formatLabel(statusValue)}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block text-sm font-medium text-brand-black">
                  Notes
                  <textarea
                    value={selectedVmDraft.notes}
                    onChange={(event) =>
                      setSelectedVmDraft((currentValue) =>
                        currentValue ? { ...currentValue, notes: event.target.value } : currentValue,
                      )
                    }
                    rows={5}
                    className="input-shell mt-2 w-full resize-none bg-brand-light outline-none"
                    disabled={!canManage}
                  />
                </label>

                {canManage ? (
                  <button type="submit" className="btn-primary w-full" disabled={activeAction !== null}>
                    {activeAction === "update" ? "Saving VM updates..." : "Save VM changes"}
                  </button>
                ) : (
                  <div className="rounded-[1.25rem] border border-brand-black/8 bg-brand-light/60 px-4 py-4 text-sm leading-6 text-brand-black/65">
                    Viewer accounts can review the lab inventory, while admins and analysts can update VM metadata.
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-5 rounded-[1.25rem] border border-brand-black/8 bg-brand-light/60 px-4 py-4 text-sm text-brand-black/65">
                Select a VM card or table row to inspect its role, status, IP placeholder, and notes.
              </div>
            )}
          </form>

          <form className="panel p-5" onSubmit={handleCreateVm}>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-orange">
              Register lab VM
            </p>
            <h3 className="mt-2 text-xl font-semibold text-brand-black">Add to inventory</h3>
            <p className="mt-3 text-sm leading-6 text-brand-black/65">
              Capture presentation-ready VM metadata for the classroom environment. This records inventory details only.
            </p>

            <div className="mt-5 space-y-4">
              <label className="block text-sm font-medium text-brand-black">
                VM name
                <input
                  type="text"
                  value={newVmForm.vm_name}
                  onChange={(event) =>
                    setNewVmForm((currentValue) => ({
                      ...currentValue,
                      vm_name: event.target.value,
                    }))
                  }
                  className="input-shell mt-2 w-full bg-brand-light outline-none"
                  disabled={!canManage}
                  placeholder="lab-collector-02"
                />
              </label>

              <label className="block text-sm font-medium text-brand-black">
                Role
                <input
                  type="text"
                  value={newVmForm.role}
                  onChange={(event) =>
                    setNewVmForm((currentValue) => ({
                      ...currentValue,
                      role: event.target.value,
                    }))
                  }
                  className="input-shell mt-2 w-full bg-brand-light outline-none"
                  disabled={!canManage}
                  placeholder="Log Collector VM"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-medium text-brand-black">
                  OS type
                  <input
                    type="text"
                    value={newVmForm.os_type}
                    onChange={(event) =>
                      setNewVmForm((currentValue) => ({
                        ...currentValue,
                        os_type: event.target.value,
                      }))
                    }
                    className="input-shell mt-2 w-full bg-brand-light outline-none"
                    disabled={!canManage}
                    placeholder="Ubuntu Server 22.04"
                  />
                </label>

                <label className="block text-sm font-medium text-brand-black">
                  IP placeholder
                  <input
                    type="text"
                    value={newVmForm.ip_address}
                    onChange={(event) =>
                      setNewVmForm((currentValue) => ({
                        ...currentValue,
                        ip_address: event.target.value,
                      }))
                    }
                    className="input-shell mt-2 w-full bg-brand-light outline-none"
                    disabled={!canManage}
                    placeholder="10.10.0.40"
                  />
                </label>
              </div>

              <label className="block text-sm font-medium text-brand-black">
                Status
                <select
                  value={newVmForm.status}
                  onChange={(event) =>
                    setNewVmForm((currentValue) => ({
                      ...currentValue,
                      status: event.target.value as VirtualMachineStatus,
                    }))
                  }
                  className="input-shell mt-2 w-full bg-brand-light outline-none"
                  disabled={!canManage}
                >
                  {virtualMachineStatusOptions.map((statusValue) => (
                    <option key={statusValue} value={statusValue}>
                      {formatLabel(statusValue)}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block text-sm font-medium text-brand-black">
                Notes
                <textarea
                  value={newVmForm.notes}
                  onChange={(event) =>
                    setNewVmForm((currentValue) => ({
                      ...currentValue,
                      notes: event.target.value,
                    }))
                  }
                  rows={4}
                  className="input-shell mt-2 w-full resize-none bg-brand-light outline-none"
                  disabled={!canManage}
                  placeholder="Hosts archived logs for the weekly project presentation."
                />
              </label>

              {canManage ? (
                <button type="submit" className="btn-secondary w-full" disabled={activeAction !== null}>
                  {activeAction === "create" ? "Adding lab VM..." : "Add lab VM"}
                </button>
              ) : (
                <div className="rounded-[1.25rem] border border-brand-black/8 bg-brand-light/60 px-4 py-4 text-sm leading-6 text-brand-black/65">
                  Viewer accounts can inspect the seeded lab topology, while admins and analysts can add new inventory entries for demos.
                </div>
              )}
            </div>
          </form>
        </div>
      </div>
    </SectionCard>
  );
}
