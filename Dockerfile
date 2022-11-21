ARG MODE=label

ARG DONE_SOON_VENV=/opt/done_soon-venv
ARG DONE_SOON_PYTHON=${DONE_SOON_VENV}/bin/python
ARG DONE_SOON_PIP=${DONE_SOON_VENV}/bin/pip
ARG MODDED_CHUFFED_INSTALL_PREFIX=/usr/share/minizinc/solvers

ARG BASE_IMAGE=ubuntu:20.04
ARG MINIZINCVERSION=2.6.4

ARG DEBIAN_FRONTEND=noninteractive

FROM ${BASE_IMAGE} AS with_python_pip
ARG DONE_SOON_VENV
ENV PIP_ROOT_USER_ACTION=ignore
ADD https://bootstrap.pypa.io/get-pip.py get-pip.py
# Install python3.10
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install software-properties-common -y && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get install -y \
        python3.10 \
        python3.10-venv && \
    # Install pip
    python3.10 get-pip.py && \
    rm get-pip.py && \
    python3.10 -m venv ${DONE_SOON_VENV}


FROM ${BASE_IMAGE} AS with_minizinc
ARG MINIZINCVERSION
# Install MiniZinc
ADD https://github.com/MiniZinc/MiniZincIDE/releases/download/${MINIZINCVERSION}/MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz
RUN tar xf MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz && \
    rm MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64.tgz


FROM ${BASE_IMAGE} AS with_modded_chuffed
ARG rootdir
ARG MODDED_CHUFFED_INSTALL_PREFIX
COPY ./chuffed ${rootdir}/chuffed
WORKDIR ${rootdir}/chuffed/build
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive \
    apt-get install -y \
        build-essential \
        cmake && \
    cmake -DCMAKE_INSTALL_PREFIX:PATH=${MODDED_CHUFFED_INSTALL_PREFIX} .. && \
    cmake --build . -j $(nproc) && \
    cmake --build . --target install -j $(nproc)


FROM with_python_pip AS generate_requirements_txts
ARG rootdir
# Install poetry separated from system interpreter
ENV POETRY_VERSION=1.2.0
ENV POETRY_VENV=/opt/poetry-venv
RUN python3.10 -m venv ${POETRY_VENV} && \
    $POETRY_VENV/bin/pip install -U setuptools && \
    $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}
ENV PATH="${PATH}:${POETRY_VENV}/bin"
WORKDIR ${rootdir}
COPY ./pyproject.toml .
COPY ./poetry.lock .
RUN poetry export --with=download -o requirements-download.txt && \
    poetry export -o requirements.txt && \
    rm ./pyproject.toml ./poetry.lock


FROM with_python_pip AS with_problems
ARG rootdir
ARG DONE_SOON_PYTHON
ARG DONE_SOON_PIP
WORKDIR ${rootdir}
COPY --from=generate_requirements_txts ${rootdir}/requirements-download.txt .
COPY ./problems/download.py ${rootdir}/problems/
RUN ${DONE_SOON_PIP} install -r requirements-download.txt && \
    ${DONE_SOON_PYTHON} problems/download.py --destination problems/problem_sets


FROM with_python_pip AS with_dependencies
ARG rootdir
ARG DONE_SOON_PIP
WORKDIR ${rootdir}
COPY --from=generate_requirements_txts ${rootdir}/requirements.txt .
RUN ${DONE_SOON_PIP} install -r requirements.txt


FROM with_problems AS seed_db
ARG rootdir
ARG DONE_SOON_PIP
ARG DONE_SOON_PYTHON
WORKDIR ${rootdir}
COPY --from=generate_requirements_txts ${rootdir}/requirements.txt .
RUN ${DONE_SOON_PIP} install -r requirements.txt
COPY ./done_soon/ ./done_soon/
ENV PYTHONPATH="${PYTHONPATH}:${rootdir}" DONE_SOON_PYTHON=${DONE_SOON_PYTHON} ROOTDIR=${rootdir}
CMD ${DONE_SOON_PYTHON} ${ROOTDIR}/done_soon/data_generation/db/scripts/create_initial_db.py \
    --data problems/problem_sets --db-addr mongodb


FROM with_python_pip AS data_generator
ARG rootdir
ARG MINIZINCVERSION
ARG DONE_SOON_PYTHON
ARG MODE
ARG MODDED_CHUFFED_INSTALL_PREFIX
ARG MINIZINC_DIR="/MiniZincIDE-${MINIZINCVERSION}-bundle-linux-x86_64/"
COPY --from=with_dependencies ${DONE_SOON_VENV} ${DONE_SOON_VENV}
COPY --from=with_problems ${rootdir}/problems/ ${rootdir}/problems/
COPY --from=with_modded_chuffed ${MODDED_CHUFFED_INSTALL_PREFIX} ${MODDED_CHUFFED_INSTALL_PREFIX}
COPY --from=with_minizinc ${MINIZINC_DIR} ${MINIZINC_DIR}

# Copy the rest of the project source in
WORKDIR ${rootdir}
COPY ./done_soon ./done_soon
ENV PATH="${MINIZINC_DIR}/bin:${PATH}" PYTHONPATH="${PYTHONPATH}:${rootdir}"
ENV DONE_SOON_PYTHON=${DONE_SOON_PYTHON} ROOTDIR=${rootdir} MODE=${MODE}

WORKDIR ${rootdir}
CMD ${DONE_SOON_PYTHON} ${ROOTDIR}/done_soon/data_generation/generate_data.py  \
    --mode ${MODE} \
    --data problems/problem_sets \
    --db-addr mongodb
